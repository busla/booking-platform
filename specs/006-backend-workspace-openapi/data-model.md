# Data Model: Backend UV Workspace & OpenAPI Gateway

**Phase**: 1 - Design | **Date**: 2025-12-31 | **Spec**: [spec.md](./spec.md)

## Overview

This document defines the data types for the OpenAPI generation system. The feature does not introduce new database entities; instead, it defines:
1. Security annotation types for FastAPI routes
2. OpenAPI extension schemas for AWS API Gateway
3. Configuration types for the generation script

---

## 1. Security Annotation Types

### SecurityRequirement

Marker type for route security requirements. Used as a FastAPI dependency to annotate which routes require JWT authentication.

```python
# backend/api/src/api/security.py

from enum import Enum
from typing import ClassVar

class AuthScope(str, Enum):
    """OAuth2 scopes for JWT authorization.

    These map to Cognito user pool scopes.
    """
    OPENID = "openid"
    EMAIL = "email"
    PROFILE = "profile"
    # Add custom scopes as needed:
    # RESERVATIONS_WRITE = "reservations:write"
    # RESERVATIONS_READ = "reservations:read"


class SecurityRequirement:
    """Marker class for security annotations.

    This is NOT an actual authorizer - API Gateway handles JWT validation.
    This class marks routes for OpenAPI generation only.

    Usage:
        @app.post("/reservations", dependencies=[Depends(require_auth)])
        async def create_reservation(...):
            ...

    The dependency `require_auth` returns an instance of this class.
    """

    SCHEME_NAME: ClassVar[str] = "cognito-jwt"

    def __init__(self, scopes: list[AuthScope] | None = None):
        """Initialize security requirement.

        Args:
            scopes: Optional list of required OAuth2 scopes.
                    Empty list means authenticated but no specific scopes.
        """
        self.scopes = scopes or []
```

### Dependency Factory

```python
# backend/api/src/api/security.py (continued)

from fastapi import Request

def require_auth(scopes: list[AuthScope] | None = None):
    """Create a security requirement dependency.

    This dependency does NOT perform JWT validation (API Gateway does).
    It serves as a marker for the OpenAPI generation script to add
    security requirements to the schema.

    Args:
        scopes: Optional list of required OAuth2 scopes.

    Returns:
        Dependency function that returns SecurityRequirement.

    Example:
        # Route requiring authentication (no specific scopes)
        @app.post("/reservations", dependencies=[Depends(require_auth())])

        # Route requiring specific scope
        @app.delete("/reservations/{id}",
                    dependencies=[Depends(require_auth([AuthScope.RESERVATIONS_WRITE]))])
    """
    def _require_auth(request: Request) -> SecurityRequirement:
        # In production, API Gateway has already validated the JWT
        # by the time this runs. This is just a marker.
        return SecurityRequirement(scopes=scopes)

    return _require_auth
```

---

## 2. OpenAPI Extension Types

### AWSIntegration

Pydantic model representing the `x-amazon-apigateway-integration` extension.

```python
# backend/api/src/api/openapi_extensions.py

from typing import Literal
from pydantic import BaseModel, Field


class AWSIntegration(BaseModel):
    """AWS API Gateway Lambda proxy integration.

    Represents x-amazon-apigateway-integration for HTTP API.
    All Lambda integrations use AWS_PROXY with POST method.
    """

    type: Literal["AWS_PROXY"] = "AWS_PROXY"
    httpMethod: Literal["POST"] = "POST"
    uri: str = Field(
        ...,
        description="Lambda invocation URI: "
                    "arn:aws:apigateway:{region}:lambda:path/2015-03-31/functions/{arn}/invocations"
    )
    payloadFormatVersion: Literal["2.0"] = "2.0"

    @classmethod
    def from_lambda_arn(cls, lambda_arn: str) -> "AWSIntegration":
        """Create integration from Lambda ARN.

        Args:
            lambda_arn: Full Lambda ARN (e.g., arn:aws:lambda:eu-west-1:123456789:function:my-func)

        Returns:
            AWSIntegration with properly formatted URI.

        Raises:
            ValueError: If ARN format is invalid.
        """
        # Parse region from ARN: arn:aws:lambda:{region}:{account}:function:{name}
        parts = lambda_arn.split(":")
        if len(parts) < 4 or parts[0] != "arn" or parts[2] != "lambda":
            raise ValueError(f"Invalid Lambda ARN format: {lambda_arn}")

        region = parts[3]
        uri = f"arn:aws:apigateway:{region}:lambda:path/2015-03-31/functions/{lambda_arn}/invocations"

        return cls(uri=uri)
```

### JWTConfiguration

```python
# backend/api/src/api/openapi_extensions.py (continued)

class JWTConfiguration(BaseModel):
    """JWT authorizer configuration for Cognito.

    Used in x-amazon-apigateway-authorizer.jwtConfiguration.
    """

    issuer: str = Field(
        ...,
        description="Cognito issuer URL: https://cognito-idp.{region}.amazonaws.com/{userPoolId}"
    )
    audience: list[str] = Field(
        ...,
        description="List of allowed client IDs (typically one app client)"
    )

    @classmethod
    def from_cognito(cls, user_pool_id: str, client_id: str) -> "JWTConfiguration":
        """Create JWT config from Cognito identifiers.

        Args:
            user_pool_id: Cognito User Pool ID (e.g., eu-west-1_ABC123xyz)
            client_id: Cognito App Client ID

        Returns:
            JWTConfiguration with properly formatted issuer URL.
        """
        # Extract region from user pool ID (format: {region}_{id})
        region = user_pool_id.split("_")[0]
        issuer = f"https://cognito-idp.{region}.amazonaws.com/{user_pool_id}"

        return cls(issuer=issuer, audience=[client_id])
```

### AWSAuthorizer

```python
# backend/api/src/api/openapi_extensions.py (continued)

class AWSAuthorizer(BaseModel):
    """AWS API Gateway JWT authorizer.

    Represents x-amazon-apigateway-authorizer for HTTP API JWT auth.
    """

    type: Literal["jwt"] = "jwt"
    identitySource: str = "$request.header.Authorization"
    jwtConfiguration: JWTConfiguration
```

### CORSConfiguration

```python
# backend/api/src/api/openapi_extensions.py (continued)

class CORSConfiguration(BaseModel):
    """AWS API Gateway CORS configuration.

    Represents x-amazon-apigateway-cors at OpenAPI root level.
    """

    allowOrigins: list[str] = Field(
        default=["*"],
        description="Allowed origins (use specific origins in production)"
    )
    allowMethods: list[str] = Field(
        default=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        description="Allowed HTTP methods"
    )
    allowHeaders: list[str] = Field(
        default=["Content-Type", "Authorization", "X-Requested-With", "X-Amz-Date"],
        description="Allowed request headers"
    )
    exposeHeaders: list[str] = Field(
        default=["X-Request-Id"],
        description="Headers exposed to browser"
    )
    maxAge: int = Field(
        default=86400,
        description="Preflight cache duration in seconds"
    )
    allowCredentials: bool = Field(
        default=True,
        description="Whether credentials are supported"
    )
```

---

## 3. Script Configuration Types

### OpenAPIGeneratorConfig

Configuration for the OpenAPI generation script.

```python
# backend/api/scripts/generate_openapi.py

from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings


class OpenAPIGeneratorConfig(BaseSettings):
    """Configuration for OpenAPI generation script.

    Values come from environment variables or CLI arguments.
    Terraform passes these via the external data source.
    """

    # Required: Lambda integration
    lambda_arn: str = Field(
        ...,
        description="Full Lambda ARN for API integration",
        json_schema_extra={"env": "LAMBDA_ARN"}
    )

    # Required: Cognito JWT authorizer
    cognito_user_pool_id: str = Field(
        ...,
        description="Cognito User Pool ID (format: {region}_{id})",
        json_schema_extra={"env": "COGNITO_USER_POOL_ID"}
    )
    cognito_client_id: str = Field(
        ...,
        description="Cognito App Client ID",
        json_schema_extra={"env": "COGNITO_CLIENT_ID"}
    )

    # Optional: CORS configuration
    cors_allow_origins: list[str] = Field(
        default=["*"],
        description="Allowed CORS origins",
        json_schema_extra={"env": "CORS_ALLOW_ORIGINS"}
    )

    @field_validator("lambda_arn")
    @classmethod
    def validate_lambda_arn(cls, v: str) -> str:
        """Validate Lambda ARN format."""
        if not v.startswith("arn:aws:lambda:"):
            raise ValueError(f"Invalid Lambda ARN: must start with 'arn:aws:lambda:', got {v}")
        parts = v.split(":")
        if len(parts) < 7:
            raise ValueError(f"Invalid Lambda ARN: expected 7+ parts, got {len(parts)}")
        return v

    @field_validator("cognito_user_pool_id")
    @classmethod
    def validate_user_pool_id(cls, v: str) -> str:
        """Validate Cognito User Pool ID format."""
        if "_" not in v:
            raise ValueError(f"Invalid User Pool ID: expected format {{region}}_{{id}}, got {v}")
        return v

    class Config:
        env_prefix = ""
        case_sensitive = False
```

### Script Error Handling

The script outputs errors to stderr in JSON format for Terraform compatibility:

```python
# backend/api/scripts/generate_openapi.py

import sys
import json

class ScriptError(Exception):
    """Structured error for OpenAPI generation script."""

    def __init__(self, code: str, message: str, details: dict | None = None):
        self.code = code
        self.message = message
        self.details = details or {}
        super().__init__(message)

    def to_dict(self) -> dict:
        return {
            "error": True,
            "code": self.code,
            "message": self.message,
            "details": self.details,
        }

    def exit(self) -> None:
        """Print error to stderr and exit with non-zero status."""
        print(json.dumps(self.to_dict()), file=sys.stderr)
        sys.exit(1)
```

**Error Codes**:

| Code | Condition | Example |
|------|-----------|---------|
| `INVALID_INPUT` | Malformed stdin JSON | Missing required field |
| `INVALID_LAMBDA_ARN` | ARN format validation failed | ARN doesn't start with `arn:aws:lambda:` |
| `INVALID_USER_POOL_ID` | User Pool ID format invalid | Missing region prefix |
| `IMPORT_ERROR` | FastAPI app cannot be imported | Module not found |
| `GENERATION_ERROR` | OpenAPI generation failed | `get_openapi()` raised exception |

**Example Error Output** (to stderr):

```json
{
  "error": true,
  "code": "INVALID_LAMBDA_ARN",
  "message": "Invalid Lambda ARN: must start with 'arn:aws:lambda:'",
  "details": {"received": "invalid-arn-value"}
}
```

---

## 4. Workspace Package Structure

### Package Dependencies

```
shared (leaf)
├── models/         # Pydantic models (reservation, guest, etc.)
├── services/       # Business logic (dynamodb, booking, pricing)
├── tools/          # Strands tool definitions
└── No workspace dependencies

agent
├── src/agent/      # Strands agent definition
├── agent_app.py    # AgentCore Runtime entrypoint
└── Depends on: shared

api
├── src/api/        # FastAPI routes, security annotations
├── api_app.py      # FastAPI application
├── scripts/        # OpenAPI generation script
└── Depends on: shared
```

### Import Paths After Restructure

| Current Import | New Import | Package |
|---------------|------------|---------|
| `from src.models.reservation import Reservation` | `from shared.models.reservation import Reservation` | shared |
| `from src.services.dynamodb import get_dynamodb_service` | `from shared.services.dynamodb import get_dynamodb_service` | shared |
| `from src.agent import get_agent` | `from agent.booking_agent import get_agent` | agent |
| `from src.api.auth import router` | `from api.routes.auth import router` | api |

---

## 5. Route Security Classification

Based on spec clarifications, routes are classified as:

### Public Routes (No JWT Required)

| Route | Method | Reason |
|-------|--------|--------|
| `/ping` | GET | Health check |
| `/auth/callback` | GET | OAuth2 redirect |
| `/auth/session/{session_id}` | GET | Pre-auth status check |
| `/auth/refresh` | POST | Token refresh (uses refresh_token, not JWT) |

### Protected Routes (JWT Required)

| Route | Method | Reason |
|-------|--------|--------|
| `/invoke-stream` | POST | User-specific agent conversation |
| `/invoke` | POST | User-specific agent invocation |
| `/reset` | POST | User-specific conversation reset |
| `/reservations/*` | ALL | Mutation/read of user reservations |
| `/guests/*` | ALL | User-specific guest data |

**Note**: Property info, availability, and pricing queries are handled through the agent (via `/invoke-stream`), not as separate REST endpoints. The agent's tool calls access these internally.

---

## 6. Type Exports

All new types are exported from their respective packages:

```python
# api/src/api/__init__.py
from api.security import AuthScope, SecurityRequirement, require_auth
from api.openapi_extensions import (
    AWSIntegration,
    AWSAuthorizer,
    JWTConfiguration,
    CORSConfiguration,
)

__all__ = [
    "AuthScope",
    "SecurityRequirement",
    "require_auth",
    "AWSIntegration",
    "AWSAuthorizer",
    "JWTConfiguration",
    "CORSConfiguration",
]
```

---

## 7. Schema Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         OpenAPI Schema Output                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  openapi: 3.0.1                                                        │
│  info: { ... }                                                          │
│                                                                         │
│  x-amazon-apigateway-cors:  ◄──── CORSConfiguration                    │
│    allowOrigins: [...]                                                  │
│    allowMethods: [...]                                                  │
│    ...                                                                  │
│                                                                         │
│  components:                                                            │
│    securitySchemes:                                                     │
│      cognito-jwt:                                                       │
│        type: oauth2                                                     │
│        x-amazon-apigateway-authorizer:  ◄──── AWSAuthorizer            │
│          type: jwt                                                      │
│          jwtConfiguration:  ◄──── JWTConfiguration                     │
│            issuer: https://cognito-idp.{region}.../...                  │
│            audience: [...]                                              │
│                                                                         │
│  paths:                                                                 │
│    /ping:                                                               │
│      get:                                                               │
│        security: []  ◄──── Public route                                │
│        x-amazon-apigateway-integration:  ◄──── AWSIntegration          │
│          type: AWS_PROXY                                                │
│          uri: arn:aws:apigateway:...                                   │
│                                                                         │
│    /invoke-stream:                                                      │
│      post:                                                              │
│        security: [{ cognito-jwt: [] }]  ◄──── Protected route          │
│        x-amazon-apigateway-integration:  ◄──── AWSIntegration          │
│          type: AWS_PROXY                                                │
│          uri: arn:aws:apigateway:...                                   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

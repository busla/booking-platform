"""FastAPI REST API for the Booking platform.

This package contains:
- main: FastAPI application instance and configuration
- routes: API route handlers (auth, health, etc.)
- middleware: Request/response middleware components
- security: Security annotations for OpenAPI generation
- openapi_extensions: AWS API Gateway extension types
"""

__version__ = "0.1.0"

# Re-export the FastAPI app for convenience
from api.main import app

# Re-export security annotations
from api.security import AuthScope, SecurityRequirement, require_auth

# Re-export OpenAPI extension types
from api.openapi_extensions import (
    AWSAuthorizer,
    AWSIntegration,
    CORSConfiguration,
    JWTConfiguration,
)

__all__ = [
    "__version__",
    "app",
    # Security annotations
    "AuthScope",
    "SecurityRequirement",
    "require_auth",
    # OpenAPI extension types
    "AWSIntegration",
    "AWSAuthorizer",
    "JWTConfiguration",
    "CORSConfiguration",
]

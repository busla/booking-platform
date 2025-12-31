# Quickstart: Backend UV Workspace & OpenAPI Gateway

**Phase**: 1 - Design | **Date**: 2025-12-31 | **Spec**: [spec.md](./spec.md)

## Overview

This guide covers common tasks for working with the UV workspace and OpenAPI-based API Gateway.

---

## 1. Working with the UV Workspace

### Installing Dependencies

From the repository root:

```bash
# Install all workspace members
cd backend
uv sync

# Or install a specific package
uv sync --package api
uv sync --package agent
uv sync --package shared
```

### Running Commands in Package Context

```bash
# Run tests for a specific package
uv run --package api pytest tests/unit/api/

# Run the FastAPI dev server (direct UV command)
uv run --package api uvicorn api_app:app --reload --port 3001

# Or use Taskfile (recommended - handles cwd and env vars)
task backend:dev

# Run a script in package context
uv run --package api python scripts/generate_openapi.py
```

**Note**: The `task backend:dev` command in `Taskfile.yaml` wraps the uvicorn command with proper working directory and environment variable handling. Prefer Taskfile commands for consistency with project conventions.

### Adding Dependencies

```bash
# Add to a specific workspace member
cd backend/api
uv add httpx

# Add a dev dependency
uv add --dev pytest-cov

# Add a workspace dependency (in pyproject.toml)
# [tool.uv.sources]
# shared = { workspace = true }
```

---

## 2. Adding New Routes

### Protected Route (JWT Required)

Routes that require authentication use the `require_auth` dependency:

```python
# backend/api/src/api/routes/reservations.py

from fastapi import APIRouter, Depends
from api.security import require_auth

router = APIRouter(prefix="/reservations", tags=["reservations"])

@router.post("/")
async def create_reservation(
    request: CreateReservationRequest,
    _auth: None = Depends(require_auth()),  # Marks as protected
):
    """Create a new reservation.

    Requires valid JWT token in Authorization header.
    API Gateway validates the token before this handler runs.
    """
    # Implementation here - JWT is already validated
    pass


@router.get("/{reservation_id}")
async def get_reservation(
    reservation_id: str,
    _auth: None = Depends(require_auth()),
):
    """Get reservation by ID."""
    pass
```

**Key Points**:
- `require_auth()` is a **marker only** - it doesn't validate JWTs
- API Gateway handles JWT validation before the Lambda is invoked
- The `_auth` parameter is unused; it's just for OpenAPI generation

### Public Route (No Auth)

Routes without the `require_auth` dependency are public:

```python
# backend/api/src/api/routes/health.py

from fastapi import APIRouter

router = APIRouter(tags=["health"])

@router.get("/ping")
async def ping():
    """Health check endpoint - no authentication required."""
    return {"status": "ok"}
```

### Route with Scopes (Future)

For fine-grained authorization:

```python
from api.security import require_auth, AuthScope

@router.delete("/{reservation_id}")
async def delete_reservation(
    reservation_id: str,
    _auth: None = Depends(require_auth([AuthScope.RESERVATIONS_WRITE])),
):
    """Delete reservation - requires write scope."""
    pass
```

---

## 3. OpenAPI Generation

### Running Locally

The script generates OpenAPI with AWS extensions for Terraform:

```bash
cd backend

# Using test values
echo '{"lambda_arn": "arn:aws:lambda:eu-west-1:123456789012:function:booking-api", "cognito_user_pool_id": "eu-west-1_TestPool", "cognito_client_id": "test-client-id", "cors_allow_origins": "[\"*\"]"}' | \
  uv run --package api python api/scripts/generate_openapi.py
```

### Output Format

The script outputs JSON to stdout:

```json
{
  "openapi_spec": "{\"openapi\":\"3.0.1\",\"info\":{...},\"paths\":{...}}"
}
```

Note: `openapi_spec` is a JSON-encoded string (for Terraform `external` data source).

### Validating Output

Use the JSON Schema to validate:

```bash
# Requires jsonschema CLI
cat output.json | jq -r '.openapi_spec' | \
  jsonschema -i - specs/006-backend-workspace-openapi/contracts/openapi-output.schema.json
```

---

## 4. Testing

**Execution Context**: Tests must be run with proper package context to resolve workspace imports:

```bash
# From backend/ directory

# Run API tests (unit + contract)
uv run --package api pytest tests/unit/api/ tests/contract/

# Run agent tests
uv run --package agent pytest tests/integration/test_booking_flow.py

# Run shared tests (if any)
uv run --package shared pytest tests/unit/shared/

# Or use Taskfile (handles context automatically)
task backend:test
```

**Why**: The `--package` flag ensures the correct workspace member's dependencies are available. Without it, imports like `from api.security import ...` will fail with `ModuleNotFoundError`.

### Unit Tests for Security Annotations

```python
# backend/tests/unit/api/test_security.py

import pytest
from api.security import SecurityRequirement, AuthScope, require_auth

def test_security_requirement_default_no_scopes():
    """SecurityRequirement defaults to empty scopes."""
    req = SecurityRequirement()
    assert req.scopes == []

def test_security_requirement_with_scopes():
    """SecurityRequirement accepts scope list."""
    req = SecurityRequirement(scopes=[AuthScope.OPENID, AuthScope.EMAIL])
    assert len(req.scopes) == 2

def test_require_auth_returns_callable():
    """require_auth returns a dependency function."""
    dep = require_auth()
    assert callable(dep)
```

### Contract Tests for OpenAPI Output

```python
# backend/tests/contract/test_openapi_schema.py

import json
import pytest
from jsonschema import validate, ValidationError
from pathlib import Path

@pytest.fixture
def openapi_schema():
    schema_path = Path("specs/006-backend-workspace-openapi/contracts/openapi-output.schema.json")
    return json.loads(schema_path.read_text())

def test_generated_openapi_matches_schema(openapi_schema):
    """Generated OpenAPI must match the contract schema."""
    from api.scripts.generate_openapi import generate_openapi

    openapi = generate_openapi(
        lambda_arn="arn:aws:lambda:eu-west-1:123456789012:function:test",
        cognito_user_pool_id="eu-west-1_TestPool",
        cognito_client_id="test-client",
        cors_allow_origins=["*"],
    )

    # Should not raise ValidationError
    validate(instance=openapi, schema=openapi_schema)

def test_protected_routes_have_security(openapi_schema):
    """Protected routes must have cognito-jwt security."""
    from api.scripts.generate_openapi import generate_openapi

    openapi = generate_openapi(...)

    # /invoke-stream should be protected
    invoke_stream = openapi["paths"]["/invoke-stream"]["post"]
    assert invoke_stream["security"] == [{"cognito-jwt": []}]

    # /ping should be public
    ping = openapi["paths"]["/ping"]["get"]
    assert ping["security"] == []
```

### Integration Test for Workspace Imports

```python
# backend/tests/integration/test_workspace_imports.py

def test_api_can_import_shared():
    """API package can import from shared."""
    from shared.models.reservation import Reservation
    from shared.services.dynamodb import get_dynamodb_service
    assert Reservation is not None
    assert callable(get_dynamodb_service)

def test_agent_can_import_shared():
    """Agent package can import from shared."""
    from shared.tools.availability import check_availability
    from shared.models.guest import Guest
    assert check_availability is not None
    assert Guest is not None
```

---

## 5. Terraform Workflow

### Planning with OpenAPI

```bash
# From repo root
task tf:plan:dev

# Terraform will:
# 1. Run generate_openapi.py via external data source
# 2. Pass Lambda ARN, Cognito IDs as input
# 3. Use generated OpenAPI as API Gateway body
```

### Debugging OpenAPI Generation

If `terraform plan` fails on OpenAPI generation:

```bash
# Test the script directly with same inputs
cd backend
echo '{"lambda_arn": "'$(terraform output -raw lambda_arn)'", ...}' | \
  uv run --package api python api/scripts/generate_openapi.py

# Check for Python import errors
uv run --package api python -c "from api_app import app; print(app.routes)"
```

### Viewing Generated Routes

After deployment:

```bash
# List API Gateway routes
aws apigatewayv2 get-routes --api-id $(terraform output -raw api_id) | jq '.Items[].RouteKey'
```

---

## 6. Common Issues

### Import Errors After Workspace Split

**Symptom**: `ModuleNotFoundError: No module named 'src'`

**Fix**: Update imports to use package names:
```python
# Old (broken)
from src.models.reservation import Reservation

# New (correct)
from shared.models.reservation import Reservation
```

### OpenAPI Script Timeout

**Symptom**: Terraform plan hangs or times out

**Fix**: Ensure FastAPI app imports are fast:
```python
# Avoid slow imports at module level
# Move heavy initialization inside functions
```

### JWT Validation Errors

**Symptom**: 401 Unauthorized despite valid token

**Check**:
1. Cognito User Pool ID format: `{region}_{id}` (e.g., `eu-west-1_ABC123xyz`)
2. Cognito Client ID is the App Client ID (not the User Pool ID)
3. Token is in `Authorization: Bearer <token>` header

### CORS Preflight Failures

**Symptom**: Browser shows CORS errors

**Fix**: `x-amazon-apigateway-cors` handles preflight automatically. Ensure:
- Origin is in `cors_allow_origins` list
- Method is in `allowMethods` list
- Required headers are in `allowHeaders` list

---

## 7. File Reference

| File | Purpose |
|------|---------|
| `backend/pyproject.toml` | Workspace root configuration |
| `backend/api/pyproject.toml` | API package dependencies |
| `backend/api/src/api/security.py` | Security annotations |
| `backend/api/src/api/openapi_extensions.py` | AWS extension types |
| `backend/api/scripts/generate_openapi.py` | OpenAPI generation script |
| `infrastructure/modules/gateway-v2/main.tf` | API Gateway with OpenAPI body |
| `specs/.../contracts/openapi-output.schema.json` | Output validation schema |
| `specs/.../contracts/gateway-v2-interface.md` | Terraform module contract |

# Research: Backend UV Workspace & OpenAPI Gateway

**Phase**: 0 - Research | **Date**: 2025-12-31 | **Spec**: [spec.md](./spec.md)

## Summary

This document captures research findings for restructuring the backend into a UV workspace and implementing OpenAPI-driven API Gateway provisioning. Research covers UV workspace patterns, AWS API Gateway OpenAPI extensions, JWT authorizer configuration, and Terraform integration approaches.

---

## 1. UV Workspace Configuration

### Source
- [UV Documentation - Workspaces](https://docs.astral.sh/uv/concepts/workspaces/)
- Context7: `/astral-sh/uv`

### Key Findings

**Workspace Root Configuration (`pyproject.toml`)**:
```toml
[project]
name = "booking-backend"
version = "0.1.0"

[tool.uv.workspace]
members = ["agent", "api", "shared"]
```

**Workspace Member Declaration**:
Each member has its own `pyproject.toml` that can declare dependencies on other workspace members:

```toml
# agent/pyproject.toml
[project]
name = "agent"
version = "0.1.0"
dependencies = ["shared"]

[tool.uv.sources]
shared = { workspace = true }
```

```toml
# api/pyproject.toml
[project]
name = "api"
version = "0.1.0"
dependencies = ["shared"]

[tool.uv.sources]
shared = { workspace = true }
```

```toml
# shared/pyproject.toml
[project]
name = "shared"
version = "0.1.0"
# No workspace dependencies - this is the leaf package
```

**Key Patterns**:
1. `{ workspace = true }` in `[tool.uv.sources]` declares a workspace dependency
2. Single `uv.lock` file at workspace root manages all dependencies
3. `uv sync` from workspace root installs all members
4. `uv run --package <member>` runs commands in specific member context
5. Each member can have different Python version requirements (within constraints)

**Directory Structure Validated**:
```
backend/
├── pyproject.toml          # Workspace root
├── uv.lock                  # Shared lock file
├── agent/
│   └── pyproject.toml      # Workspace member
├── api/
│   └── pyproject.toml      # Workspace member
└── shared/
    └── pyproject.toml      # Workspace member (leaf)
```

### Implications for This Feature

- Root `pyproject.toml` becomes workspace coordinator only (no direct dependencies)
- Each Lambda (agent, api) gets its own build context
- `shared` package contains all cross-cutting code (models, services, tools)
- Both `agent` and `api` declare `shared` as workspace dependency

---

## 2. AWS API Gateway OpenAPI Extensions

### Source
- [AWS Docs - HTTP API OpenAPI](https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-open-api.html)
- [AWS Docs - x-amazon-apigateway-integration](https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-swagger-extensions-integration.html)

### Key Findings

**x-amazon-apigateway-integration (HTTP API Lambda Proxy)**:
```json
{
  "paths": {
    "/ping": {
      "get": {
        "responses": {
          "200": {
            "description": "Success"
          }
        },
        "x-amazon-apigateway-integration": {
          "type": "AWS_PROXY",
          "httpMethod": "POST",
          "uri": "arn:aws:apigateway:{region}:lambda:path/2015-03-31/functions/{lambda-arn}/invocations",
          "payloadFormatVersion": "2.0"
        }
      }
    }
  }
}
```

**Critical Properties for HTTP API**:
| Property | Value | Notes |
|----------|-------|-------|
| `type` | `AWS_PROXY` | Required for Lambda proxy integration |
| `httpMethod` | `POST` | Always POST for Lambda invocation |
| `uri` | Lambda invocation URI | Format: `arn:aws:apigateway:{region}:lambda:path/2015-03-31/functions/{arn}/invocations` |
| `payloadFormatVersion` | `"2.0"` | HTTP API format (not `"1.0"`) |

**x-amazon-apigateway-cors (Root Level)**:
```json
{
  "openapi": "3.0.1",
  "info": { ... },
  "x-amazon-apigateway-cors": {
    "allowOrigins": ["https://example.com", "http://localhost:3000"],
    "allowMethods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    "allowHeaders": ["Content-Type", "Authorization", "X-Requested-With"],
    "exposeHeaders": ["X-Request-Id"],
    "maxAge": 86400,
    "allowCredentials": true
  },
  "paths": { ... }
}
```

**Note**: When using `x-amazon-apigateway-cors`, individual OPTIONS routes are NOT needed. API Gateway handles preflight automatically.

### URI Format Breakdown

```
arn:aws:apigateway:{region}:lambda:path/2015-03-31/functions/{lambda-arn}/invocations
                   ^^^^^^^^                        ^^^^^^^^^^^^
                   Region from                     Full Lambda ARN
                   Lambda ARN                      e.g., arn:aws:lambda:eu-west-1:123456789:function:booking-api
```

---

## 3. JWT Authorizer Configuration

### Source
- [AWS Docs - HTTP API JWT Authorizer](https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-jwt-authorizer.html)
- [AWS Docs - x-amazon-apigateway-authorizer](https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-swagger-extensions-authorizer.html)

### Key Findings

**Security Scheme with JWT Authorizer**:
```json
{
  "components": {
    "securitySchemes": {
      "cognito-jwt": {
        "type": "oauth2",
        "flows": {},
        "x-amazon-apigateway-authorizer": {
          "type": "jwt",
          "identitySource": "$request.header.Authorization",
          "jwtConfiguration": {
            "issuer": "https://cognito-idp.{region}.amazonaws.com/{userPoolId}",
            "audience": ["{clientId}"]
          }
        }
      }
    }
  }
}
```

**Per-Operation Security**:
```json
{
  "paths": {
    "/reservations": {
      "post": {
        "security": [{ "cognito-jwt": [] }],
        "x-amazon-apigateway-integration": { ... }
      }
    },
    "/ping": {
      "get": {
        "security": [],
        "x-amazon-apigateway-integration": { ... }
      }
    }
  }
}
```

**JWT Authorizer Properties for HTTP API**:
| Property | Value | Notes |
|----------|-------|-------|
| `type` | `"jwt"` | Required for JWT authorizer (HTTP API only) |
| `identitySource` | `"$request.header.Authorization"` | Where to find the token |
| `jwtConfiguration.issuer` | Cognito issuer URL | `https://cognito-idp.{region}.amazonaws.com/{userPoolId}` |
| `jwtConfiguration.audience` | Array of client IDs | The Cognito app client ID(s) |

**Cognito Issuer URL Format**:
```
https://cognito-idp.{region}.amazonaws.com/{userPoolId}
                    ^^^^^^^^               ^^^^^^^^^^^^
                    e.g., eu-west-1        e.g., eu-west-1_ABC123xyz
```

### Security Inheritance

- **Empty array `[]`** in security scheme: Route is public (no auth required)
- **Named scheme `[{ "cognito-jwt": [] }]`**: Route requires valid JWT
- **Scopes**: Can be added inside the array for scope-based access control

---

## 4. Terraform Integration

### Source
- [Terraform AWS Provider - aws_apigatewayv2_api](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/apigatewayv2_api)

### Key Findings

**Using OpenAPI Body**:
```hcl
resource "aws_apigatewayv2_api" "main" {
  name          = "booking-api"
  protocol_type = "HTTP"

  # OpenAPI specification as body
  body = file("${path.module}/openapi.json")

  # Or using templatefile for variable interpolation
  body = templatefile("${path.module}/openapi.json.tftpl", {
    lambda_arn          = module.api_lambda.lambda_function_arn
    region              = var.aws_region
    cognito_user_pool_id = var.cognito_user_pool_id
    cognito_client_id    = var.cognito_client_id
  })
}
```

**Important**: When using `body`, do NOT create separate `aws_apigatewayv2_route` or `aws_apigatewayv2_integration` resources - they will conflict with the OpenAPI definition.

**Generating OpenAPI at Plan Time**:

Option A: Pre-generated file (checked into repo):
```hcl
body = file("${path.module}/../../backend/api/openapi.json")
```

Option B: Template file with variables:
```hcl
body = templatefile("${path.module}/openapi.json.tftpl", {
  lambda_invoke_arn = module.lambda.invoke_arn
})
```

Option C: External data source (Python script):
```hcl
data "external" "openapi" {
  program = ["python", "${path.module}/../../backend/api/scripts/generate_openapi.py"]

  query = {
    lambda_arn = module.api_lambda.lambda_function_arn
    region     = var.aws_region
    cognito_user_pool_id = var.cognito_user_pool_id
    cognito_client_id    = var.cognito_client_id
  }
}

resource "aws_apigatewayv2_api" "main" {
  name          = "booking-api"
  protocol_type = "HTTP"
  body          = data.external.openapi.result.openapi_spec
}
```

### Recommendation

**Use Option C (external data source)** because:
1. Generates OpenAPI dynamically from FastAPI during `terraform plan`
2. No manual pre-generation step required (declarative)
3. Variables (Lambda ARN, Cognito IDs) passed at plan time
4. Changes to FastAPI routes automatically detected

**External Script Requirements**:
- Must accept JSON input via stdin
- Must output JSON to stdout with `result` key
- Must be idempotent (same input = same output)

---

## 5. FastAPI OpenAPI Generation

### Source
- [FastAPI OpenAPI Documentation](https://fastapi.tiangolo.com/advanced/extending-openapi/)

### Key Findings

**Using `get_openapi()`**:
```python
from fastapi.openapi.utils import get_openapi
from api_app import app

def generate_custom_openapi():
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    # Patch with AWS extensions
    return openapi_schema
```

**Key Points**:
1. `get_openapi()` introspects routes without executing handlers
2. Returns dict that can be modified before serialization
3. Route metadata (tags, descriptions, response models) included automatically
4. Path parameters preserved in OpenAPI format (`{param}`)

### Security Annotation Pattern

Define a dependency marker (not actual auth logic):
```python
from fastapi import Depends, HTTPException

def require_jwt_auth():
    """Marker dependency - API Gateway handles actual JWT validation."""
    pass

# Usage on protected routes
@app.post("/reservations", dependencies=[Depends(require_jwt_auth)])
async def create_reservation(...):
    ...
```

Then in OpenAPI generation, detect routes with this dependency and add security:
```python
for path, path_item in openapi_schema["paths"].items():
    for method, operation in path_item.items():
        if has_jwt_dependency(operation):
            operation["security"] = [{"cognito-jwt": []}]
```

---

## 6. Lambda Permission for API Gateway

### Key Finding

When using OpenAPI body, the Lambda permission must allow all routes:

```hcl
resource "aws_lambda_permission" "apigw" {
  statement_id  = "AllowAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = module.api_lambda.lambda_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.main.execution_arn}/*/*"
  #                                                          ^^^^
  #                                              Wildcard for all routes
}
```

The `/*/*` wildcard covers all HTTP methods and all paths defined in the OpenAPI spec.

---

## 7. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| UV workspace dependency conflicts | Low | Medium | Lock file ensures reproducibility; test each member independently |
| OpenAPI generation script timeout | Low | High | Cache FastAPI introspection; script <10s goal |
| Terraform plan-time Python execution | Medium | Medium | Use `data.external` with strict output format |
| Route mismatch (FastAPI vs Gateway) | Low | High | Contract tests comparing FastAPI routes to deployed Gateway |
| Cognito issuer URL misconfiguration | Low | High | Variable validation in Terraform; output actual URLs |

---

## 8. Open Questions (Resolved)

| Question | Resolution |
|----------|------------|
| Where does JWT verification happen? | API Gateway JWT authorizer (spec clarification) |
| How to handle path parameters? | Preserved automatically by `get_openapi()` |
| CORS: individual OPTIONS or global? | Global `x-amazon-apigateway-cors` (no individual OPTIONS) |
| Shared code location? | Third `shared` workspace member (spec clarification) |

---

## 9. References

- UV Workspaces: https://docs.astral.sh/uv/concepts/workspaces/
- HTTP API OpenAPI: https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-open-api.html
- JWT Authorizer: https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-jwt-authorizer.html
- x-amazon-apigateway-authorizer: https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-swagger-extensions-authorizer.html
- Terraform aws_apigatewayv2_api: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/apigatewayv2_api
- FastAPI OpenAPI: https://fastapi.tiangolo.com/advanced/extending-openapi/

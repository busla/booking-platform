# Contract: gateway-v2 Terraform Module Interface

**Version**: 2.0.0 (breaking change from v1.x)
**Date**: 2025-12-31

## Overview

This document defines the contract for the updated `gateway-v2` Terraform module that provisions API Gateway using OpenAPI specification instead of catch-all routing.

---

## Module Location

```
infrastructure/modules/gateway-v2/
├── main.tf
├── variables.tf
├── outputs.tf
└── README.md
```

---

## Input Variables

### Required Variables

| Variable | Type | Description |
|----------|------|-------------|
| `environment` | `string` | Deployment environment (`dev`, `prod`) |
| `lambda_function_arn` | `string` | ARN of the Lambda function for API integration |
| `lambda_invoke_arn` | `string` | Invocation ARN of the Lambda function |
| `cognito_user_pool_id` | `string` | Cognito User Pool ID for JWT authorizer |
| `cognito_client_id` | `string` | Cognito App Client ID for JWT audience |

### Optional Variables

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `cors_allow_origins` | `list(string)` | `["*"]` | Allowed CORS origins |
| `stage_name` | `string` | `"$default"` | API Gateway stage name |
| `auto_deploy` | `bool` | `true` | Enable auto-deploy for stage |
| `throttling_burst_limit` | `number` | `100` | API throttling burst limit |
| `throttling_rate_limit` | `number` | `50` | API throttling rate limit |

---

## Output Values

| Output | Type | Description |
|--------|------|-------------|
| `api_id` | `string` | API Gateway API ID |
| `api_endpoint` | `string` | API Gateway invoke URL |
| `execution_arn` | `string` | Execution ARN for Lambda permissions |
| `stage_id` | `string` | Default stage ID |

---

## Breaking Changes from v1.x

### Removed Resources

The following resources are **removed** when using OpenAPI body:

```hcl
# REMOVED - routes are defined in OpenAPI spec
# resource "aws_apigatewayv2_route" "default" { ... }

# REMOVED - integration is in OpenAPI spec
# resource "aws_apigatewayv2_integration" "lambda" { ... }
```

### New Variables

```hcl
# NEW - required for JWT authorizer
variable "cognito_user_pool_id" {
  type        = string
  description = "Cognito User Pool ID for JWT authorizer"
}

variable "cognito_client_id" {
  type        = string
  description = "Cognito App Client ID for JWT audience"
}
```

---

## Module Usage

### Current Usage (v1.x) - DEPRECATED

```hcl
module "gateway" {
  source = "./modules/gateway-v2"

  environment            = var.environment
  lambda_function_arn    = module.api_lambda.lambda_function_arn
  lambda_invoke_arn      = module.api_lambda.lambda_function_invoke_arn
}
```

### New Usage (v2.x)

```hcl
module "gateway" {
  source = "./modules/gateway-v2"

  environment            = var.environment
  lambda_function_arn    = module.api_lambda.lambda_function_arn
  lambda_invoke_arn      = module.api_lambda.lambda_function_invoke_arn

  # NEW: Required for JWT authorizer
  cognito_user_pool_id   = module.auth.user_pool_id
  cognito_client_id      = module.auth.client_id

  # Optional: CORS configuration
  cors_allow_origins     = var.cors_allow_origins
}
```

---

## OpenAPI Generation Contract

### External Data Source

The module uses Terraform's `external` data source to generate OpenAPI at plan time:

```hcl
data "external" "openapi" {
  program = [
    "python",
    "${path.module}/../../backend/api/scripts/generate_openapi.py"
  ]

  query = {
    lambda_arn           = var.lambda_function_arn
    cognito_user_pool_id = var.cognito_user_pool_id
    cognito_client_id    = var.cognito_client_id
    cors_allow_origins   = jsonencode(var.cors_allow_origins)
  }
}
```

### Script Input (stdin)

The script receives JSON input via stdin:

```json
{
  "lambda_arn": "arn:aws:lambda:eu-west-1:123456789:function:booking-api",
  "cognito_user_pool_id": "eu-west-1_ABC123xyz",
  "cognito_client_id": "1234567890abcdefghij",
  "cors_allow_origins": "[\"https://example.com\", \"http://localhost:3000\"]"
}
```

### Script Output (stdout)

The script outputs JSON to stdout:

```json
{
  "openapi_spec": "{\"openapi\":\"3.0.1\",\"info\":{...},\"paths\":{...}}"
}
```

**Note**: The `openapi_spec` value is a JSON-encoded string (escaped), not a nested object. This is required by Terraform's `external` data source.

---

## Lambda Permission

The module creates Lambda permission for all routes:

```hcl
resource "aws_lambda_permission" "apigw" {
  statement_id  = "AllowAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = var.lambda_function_arn
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.main.execution_arn}/*/*"
}
```

The `/*/*` wildcard covers:
- First `*`: Any HTTP method (GET, POST, etc.)
- Second `*`: Any path (/ping, /invoke-stream, etc.)

---

## Validation Checklist

Before deployment, verify:

- [ ] `cognito_user_pool_id` format: `{region}_{id}` (e.g., `eu-west-1_ABC123xyz`)
- [ ] `cognito_client_id` is the App Client ID (not the User Pool ID)
- [ ] `lambda_function_arn` is the full ARN (not the function name)
- [ ] Python 3.13 is available in the Terraform execution environment
- [ ] FastAPI app is importable from the script's working directory

---

## Error Scenarios

| Error | Cause | Resolution |
|-------|-------|------------|
| `Invalid Lambda ARN` | ARN doesn't match expected format | Verify Lambda ARN from module output |
| `Invalid User Pool ID` | Missing region prefix | Use full User Pool ID with region |
| `Script execution failed` | Python import error | Ensure `uv sync` completed in backend |
| `OpenAPI validation failed` | Malformed schema | Check script output for JSON errors |

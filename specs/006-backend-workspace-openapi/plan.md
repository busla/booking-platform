# Implementation Plan: Backend UV Workspace & OpenAPI Gateway

**Branch**: `006-backend-workspace-openapi` | **Date**: 2025-12-31 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/006-backend-workspace-openapi/spec.md`

## Summary

Restructure the backend into a UV workspace with three members (`agent`, `api`, `shared`) to enable independent dependency management and deployment. Then implement an OpenAPI-based API Gateway provisioning system where FastAPI routes are introspected using `get_openapi()`, patched with AWS API Gateway extensions (`x-amazon-apigateway-integration`, CORS, JWT security), and used to provision the gateway directly via Terraform instead of the current catch-all proxy pattern.

## Technical Context

**Language/Version**: Python 3.13+
**Primary Dependencies**: FastAPI, UV (workspace management), Strands Agents, boto3, Pydantic v2, Terraform
**Storage**: N/A (no new storage; existing DynamoDB tables remain unchanged)
**Testing**: pytest (with pytest-asyncio for async tests)
**Target Platform**: AWS Lambda (Python 3.13 runtime) behind API Gateway HTTP API
**Project Type**: Web application (backend restructure only; frontend unchanged)
**Performance Goals**: Maintain existing <3s agent response time; no degradation from workspace split
**Constraints**: OpenAPI generation must complete in <10s; Terraform plan must not require pre-build steps
**Scale/Scope**: ~15 FastAPI routes, 3 workspace members, 1 Terraform module update

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Test-First Development | ✅ PASS | Tests will be written for: workspace imports, OpenAPI generation script, security annotation decorator |
| II. Simplicity & YAGNI | ✅ PASS | Three workspace members is minimum viable for separation; no extra abstractions |
| III. Type Safety | ✅ PASS | All new code will use type hints; OpenAPI script typed; Pydantic models for security config |
| IV. Observability | ✅ PASS | Structured logging in OpenAPI script; API Gateway access logs retained |
| V. Incremental Delivery | ✅ PASS | P1 (workspace) → P2 (OpenAPI script) → P3 (Terraform) — each independently testable |
| VI. Technology Stack | ✅ PASS | Uses Strands, FastAPI, Terraform per constitution; no new frameworks |
| VI. UI Component Development | N/A | Backend-only feature; no UI components |

**Pre-Design Gate**: ✅ PASSED — All applicable principles satisfied.

### Post-Design Re-evaluation

*GATE: Re-check after Phase 1 design artifacts are complete.*

| Principle | Status | Post-Design Notes |
|-----------|--------|-------------------|
| I. Test-First Development | ✅ PASS | Test examples documented in quickstart.md; contract tests for OpenAPI output schema |
| II. Simplicity & YAGNI | ✅ PASS | Marker dependency pattern (SecurityRequirement) is simplest auth annotation; no actual JWT validation in FastAPI |
| III. Type Safety | ✅ PASS | Pydantic models for all OpenAPI extensions (AWSIntegration, JWTConfiguration, etc.); JSON Schema for output validation |
| IV. Observability | ✅ PASS | Structured errors via ToolError; script validation errors captured |
| V. Incremental Delivery | ✅ PASS | Three phases confirmed: workspace → OpenAPI script → Terraform module; each independently deployable |
| VI. Technology Stack | ✅ PASS | FastAPI `get_openapi()` for introspection; Terraform `external` data source for generation; no new frameworks |
| VI. UI Component Development | N/A | Backend-only feature; no UI components |

**Post-Design Gate**: ✅ PASSED — Design artifacts validate all applicable principles.

## Project Structure

### Documentation (this feature)

```text
specs/006-backend-workspace-openapi/
├── plan.md              # This file
├── research.md          # Phase 0: UV workspace patterns, OpenAPI AWS extensions research
├── data-model.md        # Phase 1: Security annotation types, OpenAPI extension schema
├── quickstart.md        # Phase 1: How to add new routes with security, run OpenAPI generation
├── contracts/           # Phase 1: OpenAPI output schema, Terraform module interface
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
backend/
├── pyproject.toml           # Root workspace configuration (UV workspace members)
├── agent/                   # Workspace member: Strands agent
│   ├── pyproject.toml       # Agent-specific dependencies (strands-agents, bedrock-agentcore)
│   └── src/
│       ├── agent/           # Agent definition (booking_agent.py)
│       └── agent_app.py     # AgentCore Runtime entrypoint
├── api/                     # Workspace member: FastAPI application
│   ├── pyproject.toml       # API-specific dependencies (fastapi, mangum, uvicorn)
│   ├── src/
│   │   ├── api/             # Route modules (auth.py, health.py)
│   │   ├── api_app.py       # FastAPI app definition
│   │   └── middleware/      # (optional) auth annotations
│   └── scripts/
│       └── generate_openapi.py  # OpenAPI generation with AWS extensions
├── shared/                  # Workspace member: Shared code
│   ├── pyproject.toml       # Shared dependencies (pydantic, boto3)
│   └── src/
│       ├── models/          # Pydantic models (reservation, guest, errors, etc.)
│       ├── services/        # Business logic (dynamodb, booking, pricing)
│       └── tools/           # Strands tool definitions
└── tests/                   # Test directory (unchanged structure)
    ├── unit/
    ├── integration/
    └── contract/

infrastructure/
└── modules/
    └── gateway-v2/
        ├── main.tf          # Updated: Use OpenAPI body instead of catch-all route
        ├── variables.tf     # Updated: Add cognito_user_pool_id, cognito_client_id
        └── outputs.tf       # Unchanged
```

**Structure Decision**: UV workspace with three members. The `shared` member contains all business logic (models, services, tools) to avoid duplication. Both `agent` and `api` declare workspace dependencies on `shared`. This is the minimum separation that achieves independent Lambda packaging.

## Complexity Tracking

> No Constitution violations requiring justification.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| — | — | — |

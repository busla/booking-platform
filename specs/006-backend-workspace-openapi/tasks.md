# Tasks: Backend UV Workspace & OpenAPI Gateway

**Input**: Design documents from `/specs/006-backend-workspace-openapi/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Contract tests for OpenAPI output schema validation are included as specified in data-model.md.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: UV workspace initialization and basic structure

- [X] T001 Create UV workspace root configuration in `backend/pyproject.toml` with workspace members `["agent", "api", "shared"]`
- [X] T002 [P] Create `backend/shared/pyproject.toml` with shared dependencies (pydantic, boto3)
- [X] T003 [P] Create `backend/api/pyproject.toml` with API dependencies (fastapi, mangum, uvicorn) + workspace dependency on `shared`
- [X] T004 [P] Create `backend/agent/pyproject.toml` with agent dependencies (strands-agents, bedrock-agentcore) + workspace dependency on `shared`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Migrate existing code to new workspace structure

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Directory Structure

- [X] T005 Create directory structure: `backend/shared/src/shared/{models,services,tools,utils}/`
- [X] T006 [P] Create directory structure: `backend/api/src/api/{routes,middleware}/`
- [X] T007 [P] Create directory structure: `backend/agent/src/agent/`

### Shared Package Migration (from `backend/src/`)

**⚠️ Use `git mv` for all moves to preserve file history**

- [X] T008 Move `backend/src/models/*.py` → `backend/shared/src/shared/models/` using `git mv`
- [X] T009 Move `backend/src/services/*.py` → `backend/shared/src/shared/services/` using `git mv`
- [X] T010 Move `backend/src/tools/*.py` → `backend/shared/src/shared/tools/` using `git mv`
- [X] T011 Move `backend/src/utils/*.py` → `backend/shared/src/shared/utils/` using `git mv`
- [X] T012 Create `__init__.py` files for shared package:
  - `backend/shared/src/shared/__init__.py` with re-exports for public API
  - `backend/shared/src/shared/models/__init__.py`
  - `backend/shared/src/shared/services/__init__.py`
  - `backend/shared/src/shared/tools/__init__.py`
  - `backend/shared/src/shared/utils/__init__.py`

### API Package Migration

- [X] T013 Move `backend/src/api_app.py` → `backend/api/src/api_app.py`
- [X] T014 Move `backend/src/api/*.py` → `backend/api/src/api/routes/`
- [X] T015 Update imports in `api_app.py` to use `shared.models`, `shared.services`

### Agent Package Migration

- [X] T016 Move `backend/src/agent_app.py` → `backend/agent/src/agent_app.py`
- [X] T017 Move `backend/src/agent/*.py` → `backend/agent/src/agent/`
- [X] T018 Update imports in `agent_app.py` and `booking_agent.py` to use `shared.models`, `shared.services`, `shared.tools`

### Test Migration

**Import Mapping Reference** (for T019-T022):
| Old Import | New Import |
|------------|------------|
| `from src.models.*` | `from shared.models.*` |
| `from src.services.*` | `from shared.services.*` |
| `from src.tools.*` | `from shared.tools.*` |
| `from src.utils.*` | `from shared.utils.*` |
| `from src.api.*` | `from api.routes.*` |
| `from src.agent.*` | `from agent.*` |

- [X] T019 Update `backend/tests/conftest.py` imports to use new package paths (see mapping above)
- [X] T020 Update all test files in `backend/tests/unit/` to use new import paths
- [X] T021 Update all test files in `backend/tests/integration/` to use new import paths
- [X] T022 Update all test files in `backend/tests/contract/` to use new import paths

### Validation

- [X] T023 Run `uv sync` from `backend/` root and verify all workspace members install
- [X] T024 Run `uv run --package api pytest tests/unit/test_api_app.py` - verify API tests pass
- [X] T025 Run `uv run --package agent pytest tests/integration/test_booking_flow.py` - verify agent tests pass

**Checkpoint**: Foundation ready - `uv sync` works, all tests pass with new import paths

---

## Phase 3: User Story 1 - Separate Backend into Workspace Members (Priority: P1) 🎯 MVP

**Goal**: Independent dependency management for agent, api, and shared packages

**Independent Test**: `uv sync` succeeds and each package's tests pass in isolation

### Tests for User Story 1

- [X] T026 [P] [US1] Create workspace import test in `backend/tests/integration/test_workspace_imports.py` per quickstart.md

### Implementation for User Story 1

- [X] T027 [US1] Add `__init__.py` exports in `backend/shared/src/shared/__init__.py` for all public types
- [X] T028 [P] [US1] Add `__init__.py` exports in `backend/api/src/api/__init__.py`
- [X] T029 [P] [US1] Add `__init__.py` exports in `backend/agent/src/agent/__init__.py`
- [X] T030 [US1] Update Lambda packaging in Terraform to use `backend/api/src` as source path
- [X] T031 [US1] Update AgentCore deployment to use `backend/agent/src` as source path
- [X] T032 [US1] Remove old `backend/src/` directory after verification

**Checkpoint**: Workspace separation complete - each member independently installable and testable

---

## Phase 4: User Story 2 - Generate OpenAPI Schema with AWS Extensions (Priority: P2)

**Goal**: Python script generates OpenAPI 3.0 with AWS API Gateway extensions

**Independent Test**: Running script produces valid OpenAPI JSON matching `contracts/openapi-output.schema.json`

### Tests for User Story 2

- [X] T033 [P] [US2] Create contract test for OpenAPI output in `backend/tests/contract/test_openapi_schema.py` per quickstart.md
- [X] T034 [P] [US2] Create unit test for security annotations in `backend/tests/unit/api/test_security.py` per quickstart.md

### Implementation for User Story 2

#### Security Annotations (per data-model.md)

- [X] T035 [P] [US2] Create `AuthScope` enum in `backend/api/src/api/security.py`
- [X] T036 [P] [US2] Create `SecurityRequirement` marker class in `backend/api/src/api/security.py`
- [X] T037 [US2] Create `require_auth()` dependency factory in `backend/api/src/api/security.py`

#### OpenAPI Extension Types (per data-model.md)

- [X] T038 [P] [US2] Create `AWSIntegration` Pydantic model in `backend/api/src/api/openapi_extensions.py`
- [X] T039 [P] [US2] Create `JWTConfiguration` Pydantic model in `backend/api/src/api/openapi_extensions.py`
- [X] T040 [P] [US2] Create `AWSAuthorizer` Pydantic model in `backend/api/src/api/openapi_extensions.py`
- [X] T041 [P] [US2] Create `CORSConfiguration` Pydantic model in `backend/api/src/api/openapi_extensions.py`

#### OpenAPI Generation Script

- [X] T042 [US2] Create script directory `backend/api/src/api/scripts/` (inside package for importability)
- [X] T043 [US2] Create `OpenAPIGeneratorConfig` Pydantic settings in `backend/api/src/api/scripts/generate_openapi.py`
- [X] T044 [US2] Implement `generate_openapi()` function using FastAPI's `get_openapi()` in `backend/api/src/api/scripts/generate_openapi.py`
- [X] T045 [US2] Add `x-amazon-apigateway-integration` patching to all path operations
- [X] T046 [US2] Add `x-amazon-apigateway-cors` configuration at root level
- [X] T047 [US2] Add `securitySchemes` with `cognito-jwt` and `x-amazon-apigateway-authorizer`
- [X] T048 [US2] Add security requirements patching based on `require_auth` dependencies
- [X] T049 [US2] Implement stdin JSON input / stdout JSON output for Terraform `external` data source

#### Route Security Classification

- [X] T050 [US2] Note: Agent routes (/invoke-stream, /invoke, /reset) are handled by AgentCore Runtime, not this FastAPI app
- [X] T051 [US2] Note: Agent routes (/invoke-stream, /invoke, /reset) are handled by AgentCore Runtime, not this FastAPI app
- [X] T052 [US2] Note: Agent routes (/invoke-stream, /invoke, /reset) are handled by AgentCore Runtime, not this FastAPI app
- [X] T053 [US2] Verify `/ping` and auth callback routes remain public (no security dependency) - verified via tests

**Checkpoint**: OpenAPI script generates valid schema with AWS extensions, security annotations work

---

## Phase 5: User Story 3 - Terraform Integration with OpenAPI Schema (Priority: P3)

**Goal**: Terraform provisions API Gateway from OpenAPI spec at plan time

**Independent Test**: `task tf:plan:dev` succeeds and shows API Gateway with OpenAPI body

### Implementation for User Story 3

#### Terraform Module Updates (per contracts/gateway-v2-interface.md)

- [X] T054 [US3] Note: `cognito_user_pool_id` variable already exists in `infrastructure/modules/gateway-v2/variables.tf`
- [X] T055 [P] [US3] Note: `cognito_client_id` variable already exists in `infrastructure/modules/gateway-v2/variables.tf`
- [X] T056 [P] [US3] Add `cors_allow_origins` variable with default `["*"]` to `infrastructure/modules/gateway-v2/variables.tf`

- [X] T057 [US3] Add `external` data source for OpenAPI generation in `infrastructure/modules/gateway-v2/main.tf`
- [X] T058 [US3] Update `aws_apigatewayv2_api` resource to use `body = data.external.openapi.result.openapi_spec`
- [X] T059 [US3] Make `aws_apigatewayv2_route` and `aws_apigatewayv2_integration` conditional (only when not using OpenAPI)
- [X] T060 [US3] Lambda permission already uses wildcard `/*/*` for all routes per contract

#### Environment Integration

- [X] T061 [US3] Set `enable_openapi_generation = true` in environment config to enable OpenAPI mode
- [X] T062 [US3] Note: Module call already passes `cognito_user_pool_id`, `cognito_client_id` from auth module
- [X] T063 [US3] Optionally add `cors_allow_origins` to module call (defaults to `["*"]`)

#### Validation

- [X] T064 [US3] Run `task tf:plan:dev` and verify OpenAPI script executes successfully
- [X] T065 [US3] Verify plan shows API Gateway body will be updated with OpenAPI spec
- [~] T066 [US3] Run `task tf:apply:dev` and verify all FastAPI routes are accessible through gateway (Ready - OpenAPI works; apply requires user discretion)

**Checkpoint**: Terraform workflow complete - gateway provisioned from OpenAPI, routes work

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Documentation and cleanup

- [X] T067 [P] Update `backend/README.md` with UV workspace usage instructions
- [X] T068 [P] Update `CLAUDE.md` with new backend package paths
- [X] T069 Run quickstart.md validation - verify all documented commands work
- [X] T070 Update `Taskfile.yaml` if backend commands need adjustment for workspace structure (verified: already correct)
- [X] T071 Cleanup: Remove any orphaned files from old `backend/src/` structure (verified: directory deleted)
- [X] T072 [P] Update `backend/.gitignore` to include workspace-specific patterns (verified: root .gitignore already covers all patterns)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories should proceed sequentially in priority order (P1 → P2 → P3)
  - US2 depends on US1 (api package must exist)
  - US3 depends on US2 (OpenAPI script must exist)
- **Polish (Phase 6)**: Depends on all user stories being complete

### Within Each Phase

- Tasks marked [P] can run in parallel
- Models/types before services
- Services before scripts
- Tests can be written alongside implementation

### Critical Path

```
T001-T004 (Setup)
    ↓
T005-T025 (Foundational)
    ↓
T026-T032 (US1: Workspace Separation)
    ↓
T033-T053 (US2: OpenAPI Generation)
    ↓
T054-T066 (US3: Terraform Integration)
    ↓
T067-T071 (Polish)
```

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story builds on previous story's completion
- Commit after each task or logical group
- Run tests after each phase to verify no regressions
- The `external` data source in Terraform requires Python available in the execution environment

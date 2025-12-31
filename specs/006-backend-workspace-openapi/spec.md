# Feature Specification: Backend UV Workspace & OpenAPI Gateway

**Feature Branch**: `006-backend-workspace-openapi`
**Created**: 2025-12-31
**Status**: Draft
**Input**: User description: "Separate the backend into an agent and fastapi uv workspace members, with their own pyproject.toml. When that is done, update the gateway-v2 module so it runs a python script that outputs the fastapi openapi schema and patches it so it can be used to provision the apigateway using openapi schema instead of proxying all endpoints to the fastapi lambda."

## Clarifications

### Session 2025-12-31

- Q: How should JWT/authorization be handled for protected routes? → A: FastAPI SHALL NOT handle JWT verification; API Gateway authorizer handles it. FastAPI routes only annotate/decorate which routes require Cognito JWT/scopes, reflected in OpenAPI schema via security schemes.
- Q: Which FastAPI routes should require JWT authentication? → A: Only mutation/user-specific routes (reservations, guest data); public routes (ping, property info) remain open.
- Q: How should the API Gateway JWT authorizer reference Cognito? → A: Accept Cognito User Pool ID/Client ID as module input variables from existing auth module outputs.
- Q: How should shared code (models, services) be structured in the UV workspace? → A: Create a third `shared` workspace member; both `agent` and `api` depend on it via workspace dependencies.
- Q: Where should the OpenAPI generation script be located? → A: In the `api` workspace member (e.g., `backend/api/scripts/generate_openapi.py`).
- Q: What traffic does the API Gateway handle? → A: FastAPI REST endpoints only (health, auth, property info); AgentCore Runtime is invoked directly by frontend via `@aws-sdk/client-bedrock-agentcore` or HTTP fetch, bypassing API Gateway entirely.
- Q: How are the workspace members deployed? → A: Two deployments: `api` → Lambda (behind API Gateway); `agent` → AgentCore Runtime (separate managed service).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Separate Backend into Workspace Members (Priority: P1)

As a developer, I need the backend code to be organized into separate UV workspace members (agent, api, and shared) so that:
- The agent code and API code have independent dependency management
- Shared code (models, services, utilities) is centralized and reusable
- Changes to one component don't affect the other's dependencies
- Each component can be built and packaged independently for deployment

**Why this priority**: This is foundational restructuring required before the OpenAPI gateway work can proceed. Clean separation enables independent Lambda packaging and clearer dependency boundaries.

**Independent Test**: Can be verified by running `uv sync` from the backend root successfully, with each member's tests passing in isolation.

**Acceptance Scenarios**:

1. **Given** the current monolithic backend structure, **When** I run `uv sync` from the backend root, **Then** all three workspace members (agent, api, shared) are installed with their respective dependencies.
2. **Given** the api workspace member, **When** I import only api-specific modules, **Then** the import succeeds without loading agent dependencies (shared dependencies are allowed).
3. **Given** the agent workspace member, **When** I import only agent-specific modules, **Then** the import succeeds without loading api dependencies (shared dependencies are allowed).
4. **Given** either workspace member, **When** I run tests for that member, **Then** tests pass without requiring the other member's code (shared code is available).

---

### User Story 2 - Generate OpenAPI Schema with AWS Extensions (Priority: P2)

As a DevOps engineer, I need a Python script that extracts the FastAPI OpenAPI schema and patches it with AWS API Gateway extensions so that:
- The API Gateway can be provisioned directly from the OpenAPI definition
- Each endpoint routes to the FastAPI Lambda with proper integration configuration
- Infrastructure changes are fully declarative and reproducible

**Why this priority**: Once the workspace separation is complete, this enables the OpenAPI-driven gateway provisioning which replaces the catch-all proxy pattern.

**Independent Test**: Running the Python script produces a valid OpenAPI 3.0 JSON file with `x-amazon-apigateway-integration` extensions on all paths, which can be validated using the AWS CLI import validation.

**Acceptance Scenarios**:

1. **Given** the FastAPI application, **When** I run the OpenAPI generation script, **Then** it outputs a valid OpenAPI 3.0 specification in JSON format.
2. **Given** the generated OpenAPI spec, **When** I inspect any path operation (GET, POST, etc.), **Then** it contains an `x-amazon-apigateway-integration` extension with type `AWS_PROXY`, correct Lambda URI format, and `payloadFormatVersion: "2.0"`.
3. **Given** the script receives the Lambda ARN as input, **When** it generates the OpenAPI spec, **Then** all integration URIs reference the correct Lambda ARN in the format `arn:aws:apigateway:{region}:lambda:path/2015-03-31/functions/{lambda-arn}/invocations`.
4. **Given** the generated OpenAPI spec, **When** I inspect the root level, **Then** it contains `x-amazon-apigateway-cors` configuration matching the current CORS settings.

---

### User Story 3 - Terraform Integration with OpenAPI Schema (Priority: P3)

As a platform engineer, I need Terraform to generate the OpenAPI schema during plan/apply so that:
- The API Gateway is provisioned from the OpenAPI definition rather than individual route resources
- Routes are automatically updated when FastAPI endpoints change
- The infrastructure remains fully declarative without manual schema generation steps

**Why this priority**: This completes the integration by making the OpenAPI schema generation part of the Terraform workflow, ensuring the gateway definition stays synchronized with the FastAPI routes.

**Independent Test**: Running `task tf:plan:dev` shows the API Gateway will be created/updated using the OpenAPI body, and `task tf:apply:dev` successfully provisions the gateway with all FastAPI routes accessible.

**Acceptance Scenarios**:

1. **Given** the gateway-v2 Terraform module, **When** I run `terraform plan`, **Then** it executes the Python script and generates the OpenAPI schema without errors.
2. **Given** a change to FastAPI routes, **When** I run `terraform plan`, **Then** it detects the route change and shows the API Gateway body will be updated.
3. **Given** the Lambda ARN output from the Lambda module, **When** Terraform generates the OpenAPI schema, **Then** the Lambda ARN is correctly interpolated into the integration URIs.
4. **Given** the complete Terraform apply, **When** I invoke any FastAPI endpoint through the API Gateway, **Then** the request reaches the Lambda and returns the expected response.

---

### Edge Cases

- What happens when FastAPI has no routes defined? The script should produce a valid but empty paths object.
- How does the system handle routes with path parameters (e.g., `/users/{id}`)? Path parameters should be preserved in OpenAPI format.
- What happens if the Lambda ARN input is empty or invalid? The script should fail fast with a clear error message.
- How are OPTIONS routes handled for CORS? CORS is configured at the API level via `x-amazon-apigateway-cors`, individual OPTIONS routes are not needed.
- What happens when a FastAPI endpoint has dependencies that aren't available during schema generation? The script uses FastAPI's `get_openapi()` which doesn't execute route handlers, only inspects metadata.
- How are unauthenticated requests to protected routes handled? API Gateway JWT authorizer returns 401 before reaching Lambda; FastAPI never sees unauthorized requests.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST restructure the backend into a UV workspace with three members (`agent`, `api`, `shared`), each with its own `pyproject.toml`.
- **FR-002**: The `api` workspace member MUST contain only FastAPI-related code and dependencies (routes, handlers, middleware); it deploys as a Lambda function behind API Gateway.
- **FR-003**: The `agent` workspace member MUST contain only Strands agent code and dependencies (agent definition, tools, prompts); it deploys to AgentCore Runtime (separate from API Gateway).
- **FR-004**: Shared code (models, services, utilities) MUST be placed in a third `shared` workspace member; both `agent` and `api` members MUST declare workspace dependencies on `shared`.
- **FR-005**: System MUST provide a Python script located in the `api` workspace member (e.g., `backend/api/scripts/generate_openapi.py`) that generates an OpenAPI 3.0 specification from the FastAPI application using `fastapi.openapi.utils.get_openapi()`.
- **FR-006**: The generated OpenAPI specification MUST include `x-amazon-apigateway-integration` extensions on all path operations with `type: AWS_PROXY`, `httpMethod: POST`, and `payloadFormatVersion: "2.0"`.
- **FR-007**: The OpenAPI generation script MUST accept the Lambda ARN as a command-line argument or environment variable and format it correctly in the integration URI.
- **FR-008**: The gateway-v2 Terraform module MUST use `terraform_data` to execute the Python script during plan/apply.
- **FR-009**: The API Gateway resource MUST use the `body` argument with the generated OpenAPI JSON to define routes instead of individual `aws_apigatewayv2_route` resources.
- **FR-010**: The Lambda permission resource MUST allow API Gateway to invoke the Lambda for all routes defined in the OpenAPI specification.
- **FR-011**: FastAPI routes requiring authentication (mutation/user-specific: reservations, guest data) MUST be annotated with decorators/dependencies that declare required Cognito JWT scopes; public routes (ping, property info) SHALL NOT require authentication. FastAPI SHALL NOT perform JWT verification itself.
- **FR-012**: The OpenAPI generation script MUST include `securitySchemes` and per-operation `security` requirements in the output, reflecting FastAPI route authentication annotations.
- **FR-013**: The gateway-v2 Terraform module MUST accept `cognito_user_pool_id` and `cognito_client_id` as input variables and configure an API Gateway JWT authorizer using these values, referenced by the OpenAPI security scheme.

### Key Entities *(include if feature involves data)*

- **UV Workspace**: Root project configuration managing multiple member packages with shared lock file.
- **Workspace Member**: Independent Python package (agent or api) with its own pyproject.toml and dependencies.
- **OpenAPI Specification**: JSON document describing the API structure with AWS-specific extensions.
- **API Gateway Integration**: AWS extension defining how each route connects to the Lambda backend.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Backend code is successfully split into two workspace members, with each member's tests passing independently (100% test pass rate for both members).
- **SC-002**: Running `uv sync` from backend root installs all dependencies for both members without conflicts.
- **SC-003**: The OpenAPI generation script produces a valid JSON file that passes AWS API Gateway import validation with zero errors.
- **SC-004**: All existing FastAPI endpoints remain accessible through the API Gateway after migration (100% endpoint parity).
- **SC-005**: Terraform plan/apply completes without manual intervention, and the gateway is provisioned from the OpenAPI spec.
- **SC-006**: Adding a new FastAPI route and running `task tf:apply:dev` automatically provisions that route in the API Gateway without additional configuration.

## Assumptions

- The existing FastAPI application structure follows standard patterns that `get_openapi()` can introspect.
- UV workspaces support the required dependency isolation without circular dependency issues.
- The Lambda ARN is available as a Terraform output before the OpenAPI script runs (may require staged apply or local-exec triggers).
- The existing CORS configuration can be translated to `x-amazon-apigateway-cors` without loss of functionality.
- Path parameters in FastAPI routes (e.g., `/items/{item_id}`) are compatible with API Gateway path parameter syntax.
- **The API Gateway handles FastAPI REST endpoints only**; AgentCore Runtime traffic is NOT proxied through the gateway. The frontend invokes AgentCore directly using `@aws-sdk/client-bedrock-agentcore` or HTTP fetch with SigV4 signing.

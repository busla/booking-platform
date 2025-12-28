# Implementation Plan: Agent-First Vacation Rental Booking Platform

**Branch**: `001-agent-booking-platform` | **Date**: 2025-12-27 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-agent-booking-platform/spec.md`

## Summary

Build an AI agent-driven vacation rental booking platform where the conversational agent IS the primary website interface. Users interact naturally with the agent to check availability, get pricing, view photos, and complete bookings for a single apartment in Quesada, Alicante. The technical approach uses Vercel AI SDK v6 with ai-elements for the frontend conversation UI, Strands agent framework for backend agent orchestration with MCP tools, AWS AgentCore Runtime for deployment, DynamoDB for data persistence, and AWS Cognito custom challenge flow for passwordless email verification.

## Technical Context

**Language/Version**: TypeScript 5.x (Frontend/Next.js), Python 3.12 (Backend/Strands Agent)
**Primary Dependencies**:
- Frontend: Vercel AI SDK v6 (`ai` package), ai-elements, Next.js 14+ (App Router), React 18+
- Backend: Strands Agents framework, boto3, pydantic v2
- Infrastructure: terraform-aws-agentcore module

**Package Manager**: Yarn Berry with `nodeLinker: node-modules` (frontend)

**Storage**: AWS DynamoDB (Reservations, Guests, Availability, Pricing tables)
**Testing**: Vitest (frontend), pytest (backend), Playwright (E2E)
**Target Platform**: AWS (AgentCore Runtime, DynamoDB, Cognito, CloudFront/S3)
**Project Type**: Web application (frontend + backend separation)
**Performance Goals**:
- Agent response time < 3 seconds (SC-003)
- Handle 100 concurrent conversations (SC-008)
- Booking confirmation emails within 1 minute (SC-009)

**Constraints**:
- Booking completion < 5 minutes (SC-001)
- 99.9% availability accuracy (SC-004)
- Zero double-bookings (SC-006)
- 90% questions answered without human intervention (SC-005)

**Scale/Scope**: Single apartment property, estimated 50-100 bookings/month, 10-50 concurrent users

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Test-First Development | ✅ PASS | TDD workflow defined for all user stories |
| II. Simplicity & YAGNI | ✅ PASS | Single property, mocked payments, MVP-first approach |
| III. Type Safety | ✅ PASS | TypeScript strict mode (frontend), Python type hints + pydantic v2 (backend) |
| IV. Observability | ✅ PASS | AgentCore built-in observability, structured logging, CloudWatch |
| V. Incremental Delivery | ✅ PASS | 6 user stories prioritized P1-P6 for independent delivery |
| VI. Technology Stack | ✅ PASS | Vercel AI SDK v6, Strands, terraform-aws-agentcore mandated |

**Gate Status**: ✅ All principles satisfied - proceed to Phase 0

## Project Structure

### Documentation (this feature)

```text
specs/001-agent-booking-platform/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (API schemas)
│   ├── agent-tools.json
│   └── rest-api.yaml
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
# Web Application Structure (frontend + backend)

backend/
├── src/
│   ├── agent/               # Strands agent definition
│   │   ├── __init__.py
│   │   ├── booking_agent.py # Main agent with system prompt
│   │   └── prompts/         # System prompts and templates
│   ├── tools/               # Strands native tools (@tool decorator)
│   │   ├── __init__.py
│   │   ├── availability.py  # check_availability, get_calendar
│   │   ├── pricing.py       # get_pricing, calculate_total
│   │   ├── reservations.py  # create_reservation, get/cancel/modify
│   │   ├── payments.py      # process_payment (mocked)
│   │   ├── property.py      # get_property_details, get_photos
│   │   ├── area_info.py     # get_area_info, get_recommendations
│   │   └── guest.py         # initiate_verification, verify_code, get_guest_info
│   ├── models/              # Pydantic data models
│   │   ├── __init__.py
│   │   ├── reservation.py
│   │   ├── guest.py
│   │   ├── availability.py
│   │   └── pricing.py
│   ├── services/            # Business logic layer
│   │   ├── __init__.py
│   │   ├── availability_service.py
│   │   ├── booking_service.py
│   │   ├── payment_service.py
│   │   └── notification_service.py
│   └── api/                 # FastAPI endpoints (if needed beyond AgentCore)
│       ├── __init__.py
│       └── health.py
├── tests/
│   ├── unit/
│   ├── integration/
│   └── contract/
├── pyproject.toml
└── Dockerfile

frontend/
├── src/
│   ├── app/                 # Next.js App Router
│   │   ├── layout.tsx
│   │   ├── page.tsx         # Home with agent interface
│   │   ├── api/
│   │   │   └── chat/
│   │   │       └── route.ts # AI SDK streaming endpoint
│   │   ├── pricing/
│   │   │   └── page.tsx
│   │   ├── location/
│   │   │   └── page.tsx
│   │   ├── about/
│   │   │   └── page.tsx
│   │   ├── area-guide/
│   │   │   └── page.tsx
│   │   ├── faq/
│   │   │   └── page.tsx
│   │   └── contact/
│   │       └── page.tsx
│   ├── components/
│   │   ├── agent/           # Agent UI components
│   │   │   ├── ChatInterface.tsx
│   │   │   ├── MessageBubble.tsx
│   │   │   ├── RichContentRenderer.tsx
│   │   │   ├── BookingSummaryCard.tsx
│   │   │   ├── AvailabilityCalendar.tsx
│   │   │   ├── PhotoGallery.tsx
│   │   │   └── VerificationCodeInput.tsx
│   │   ├── layout/
│   │   │   ├── Navigation.tsx
│   │   │   ├── Header.tsx
│   │   │   └── Footer.tsx
│   │   └── ui/              # Shared UI primitives
│   ├── lib/
│   │   ├── strands-provider.ts  # Custom AI SDK provider for Strands
│   │   └── auth.ts              # Cognito passwordless helpers
│   └── types/
│       └── index.ts
├── tests/
│   ├── unit/
│   └── e2e/
├── package.json
├── tsconfig.json
└── next.config.js

infrastructure/
├── main.tf              # Root module using terraform-aws-agentcore + cognito-passwordless
├── variables.tf
├── outputs.tf
└── environments/
    ├── dev.tfvars
    └── prod.tfvars
```

**Structure Decision**: Web application with clear frontend/backend separation. Frontend is a Next.js app using Vercel AI SDK v6 for the conversation UI. Backend is a Strands agent deployed to AgentCore Runtime. Infrastructure managed via terraform-aws-agentcore module. Cognito Lambda functions are **bundled within the cognito-passwordless module**, not in consumer projects—Booking only provides configuration. This structure supports independent deployment of frontend (CloudFront/S3) and backend (AgentCore), enables clear API boundaries, and aligns with the constitution's technology stack requirements.

**Terraform Execution**: All Terraform commands MUST be run via `Taskfile.yaml` at repo root—never manually. Use syntax `task tf:<action>:<env>` (e.g., `task tf:init:dev`, `task tf:plan:prod`). The Taskfile handles environment selection, backend configuration, and AWS profile binding.

**Module Path Configuration**: The `terraform-aws-agentcore` module path MUST be configured via environment variable `TF_VAR_agentcore_module_path` or in tfvars files as `agentcore_module_path`. Do NOT hardcode absolute paths in Terraform files.

### Prerequisite: cognito-passwordless Module

> ⚠️ **Before Booking implementation begins**, a new `cognito-passwordless` module MUST be created in `terraform-aws-agentcore/modules/`. The existing `cognito-user-pool` module does not support custom auth challenge flows.

```text
# To be added to terraform-aws-agentcore repository
terraform-aws-agentcore/modules/cognito-passwordless/
├── main.tf           # User pool with ALLOW_CUSTOM_AUTH, Lambda triggers
├── variables.tf      # Configuration inputs (SES email, code TTL, max attempts)
├── outputs.tf        # user_pool_id, user_pool_client_id, etc.
├── lambdas.tf        # Lambda function definitions for triggers
├── iam.tf            # IAM roles for Lambda execution + SES
├── README.md         # Module documentation
└── lambdas/          # Lambda source code (bundled with module, NOT in consumer projects)
    ├── define-auth/
    │   └── index.py  # DefineAuthChallenge trigger
    ├── create-auth/
    │   └── index.py  # CreateAuthChallenge trigger (generates code, sends via SES)
    └── verify-auth/
        └── index.py  # VerifyAuthChallengeResponse trigger
```

**Key design**: The Lambda functions are **self-contained within the module**. Consumer projects (like Booking) do NOT need to provide Lambda code—they simply configure the module with SES settings and business rules (code TTL, max attempts).

### Prerequisite: static-website Module

> ⚠️ **Before frontend deployment**, a new `static-website` module MUST be created in `terraform-aws-agentcore/modules/`. This module hosts Next.js static exports on S3 behind CloudFront.

```text
# To be added to terraform-aws-agentcore repository
terraform-aws-agentcore/modules/static-website/
├── main.tf           # Orchestrates S3, CloudFront, IAM via terraform-aws-modules
├── variables.tf      # Configuration inputs (domain, certificate_arn, origin_path)
├── outputs.tf        # cloudfront_distribution_id, s3_bucket_name, cloudfront_domain
├── versions.tf       # Provider version constraints
└── README.md         # Module documentation
```

**Key design**: The module MUST use **terraform-aws-modules** (community modules) for all resources:
- `terraform-aws-modules/s3-bucket/aws` - S3 bucket with website hosting
- `terraform-aws-modules/cloudfront/aws` - CloudFront distribution (latest stable, e.g., v6.0.2)
- `terraform-aws-modules/iam/aws` - IAM policies for S3 access

**Build & deploy orchestration**: All operations MUST stay within the Terraform domain—no external CLI commands. The module uses `terraform_data` resource with `local-exec` provisioner to:
1. Build the frontend (`yarn build` / `next build && next export`)
2. Sync build output to S3 (`aws s3 sync`)

**Cache invalidation strategy**: CloudFront invalidation is NEVER required. Next.js MUST be configured to export artifacts with **content-hash filenames** (e.g., `main-abc123.js`). CloudFront uses aggressive caching with long TTLs; cache-busting happens automatically via filename changes.

Consumer projects (like Booking) configure the module with domain settings, certificate ARN, and frontend source directory—no manual deployment commands.

## Constitution Check (Post-Design Re-evaluation)

*Re-evaluated after Phase 1 design completion (data model, contracts, quickstart)*

| Principle | Status | Post-Design Notes |
|-----------|--------|-------------------|
| I. Test-First Development | ✅ PASS | Test structure defined in quickstart.md; unit/integration/contract/E2E test directories specified |
| II. Simplicity & YAGNI | ✅ PASS | Single DynamoDB table per entity (no over-normalized design); mocked payment provider; static property/area content |
| III. Type Safety | ✅ PASS | Pydantic v2 models with strict=True for all entities; OpenAPI schema for REST endpoints |
| IV. Observability | ✅ PASS | Health check endpoint defined; structured error codes in agent-tools.json; AgentCore provides tracing |
| V. Incremental Delivery | ✅ PASS | 16 MCP tools categorized into inquiry/booking/verification; can implement tools independently |
| VI. Technology Stack | ✅ PASS | All contracts reference mandated technologies; custom Strands provider pattern documented in research.md |

**Post-Design Gate Status**: ✅ All principles satisfied - ready for Phase 2 task generation

## Complexity Tracking

> No constitution violations requiring justification.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| *None* | — | — |

## Phase 1 Deliverables Summary

| Artifact | Status | Description |
|----------|--------|-------------|
| `research.md` | ✅ Complete | Technology research for Vercel AI SDK, Strands, terraform-aws-agentcore, Cognito passwordless |
| `data-model.md` | ✅ Complete | DynamoDB schemas for 6 tables with Pydantic models and Terraform resources |
| `contracts/agent-tools.json` | ✅ Complete | Strands tool module mapping, categories, and rich content types (16 tools) |
| `contracts/rest-api.yaml` | ✅ Complete | OpenAPI 3.1 spec for chat, health, property, and auth endpoints |
| `quickstart.md` | ✅ Complete | Developer setup guide with commands for backend, frontend, and infrastructure |
| `CLAUDE.md` | ✅ Complete | Agent context file with project structure and conventions |

## Next Steps

Phase 2: Run `/speckit.tasks` to generate the implementation task list from spec.md and Phase 1 artifacts.

# Tasks: Agent-First Vacation Rental Booking Platform

**Input**: Design documents from `/specs/001-agent-booking-platform/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Tests are included per TDD workflow defined in plan.md (Vitest for frontend, pytest for backend, Playwright for E2E).

**Organization**: Tasks grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: User story label (US1-US6, FOUND for foundational)
- Exact file paths included in descriptions

## Path Conventions (Web App Structure)

- `backend/src/` - Python Strands agent
- `frontend/src/` - Next.js App Router
- `infrastructure/` - Terraform modules

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project directory structure per plan.md (backend/, frontend/, infrastructure/)
- [X] T001a [P] Adapt Taskfile.yaml for Booking with syntax `task tf:<action>:<env>` (e.g., tf:init:dev, tf:plan:prod). ALL terraform commands MUST use Taskfile
- [X] T001b [P] Initialize frontend with Yarn Berry: `yarn init -2`, configure `.yarnrc.yml` with `nodeLinker: node-modules`
- [X] T002 [P] Initialize Python backend with pyproject.toml (strands-agents, boto3, pydantic v2)
- [X] T003 [P] Initialize Next.js 14 frontend with package.json (ai, react 18, typescript strict) using Yarn Berry
- [X] T003a [P] Configure Next.js for static export with content-hash filenames in next.config.js (`output: 'export'`, ensure asset hashing enabled)
- [X] T004 [P] Configure backend linting (ruff) and type checking (mypy) in pyproject.toml
- [X] T005 [P] Configure frontend linting (eslint) and formatting (prettier) in package.json
- [X] T006 [P] Create CLAUDE.md context file at repository root with project conventions (include Taskfile requirement for terraform)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### 2A: Infrastructure Foundation

- [ ] T006a [P] [FOUND] Verify SES domain/email identity in AWS console (prerequisite for cognito-passwordless email delivery)
- [X] T007 [FOUND] Create infrastructure/main.tf with terraform-aws-agentcore module reference
- [X] T007a [P] [FOUND] Add static-website module reference in infrastructure/main.tf with terraform_data for build/deploy (PREREQUISITE: module must exist in terraform-aws-agentcore)
- [X] T008 [P] [FOUND] Create infrastructure/variables.tf with environment, namespace, AWS region
- [X] T009 [P] [FOUND] Create infrastructure/outputs.tf with cognito, agentcore, dynamodb, cloudfront outputs
- [X] T010 [P] [FOUND] Create infrastructure/environments/dev.tfvars with backend config (profile=apro-sandbox, allowed_account_ids=["195275641848"])
- [X] T011 [P] [FOUND] Create infrastructure/environments/prod.tfvars with backend config (profile/account TBD)

### 2B: DynamoDB Tables (per data-model.md)

- [X] T012 [P] [FOUND] Add DynamoDB table: booking-reservations in infrastructure/dynamodb.tf
- [X] T013 [P] [FOUND] Add DynamoDB table: booking-guests in infrastructure/dynamodb.tf
- [X] T014 [P] [FOUND] Add DynamoDB table: booking-availability in infrastructure/dynamodb.tf
- [X] T015 [P] [FOUND] Add DynamoDB table: booking-pricing in infrastructure/dynamodb.tf
- [X] T016 [P] [FOUND] Add DynamoDB table: booking-payments in infrastructure/dynamodb.tf
- [X] T017 [P] [FOUND] Add DynamoDB table: booking-verification-codes in infrastructure/dynamodb.tf

### 2C: Backend Pydantic Models (per data-model.md, FR-043)

- [X] T018 [P] [FOUND] Create Reservation model in backend/src/models/reservation.py (strict=True)
- [X] T019 [P] [FOUND] Create Guest model in backend/src/models/guest.py (strict=True)
- [X] T020 [P] [FOUND] Create Availability model in backend/src/models/availability.py (strict=True)
- [X] T021 [P] [FOUND] Create Pricing model in backend/src/models/pricing.py (strict=True)
- [X] T022 [P] [FOUND] Create Payment model in backend/src/models/payment.py (strict=True)
- [X] T023 [FOUND] Create models/__init__.py exporting all models
- [X] T023a [FOUND] Configure pydantic-to-typescript or datamodel-code-generator for TypeScript type generation from Pydantic models (FR-048)

### 2D: Backend Core Services

- [X] T024 [FOUND] Implement DynamoDB client wrapper in backend/src/services/dynamodb.py
- [X] T025 [P] [FOUND] Create AvailabilityService in backend/src/services/availability_service.py
- [X] T026 [P] [FOUND] Create BookingService with double-booking prevention in backend/src/services/booking_service.py
- [X] T027 [P] [FOUND] Create PaymentService (mocked) in backend/src/services/payment_service.py
- [X] T028 [P] [FOUND] Create NotificationService (email) in backend/src/services/notification_service.py

### 2E: Agent Foundation

- [X] T029 [FOUND] Create system prompt in backend/src/agent/prompts/system_prompt.md
- [X] T030 [FOUND] Create booking_agent.py skeleton with SlidingWindowConversationManager in backend/src/agent/booking_agent.py
- [X] T030a [FOUND] Add integration test verifying conversation context is maintained across multiple turns (FR-004)
- [X] T031 [FOUND] Create AgentCore entrypoint in backend/src/agent_app.py
- [X] T032 [FOUND] Create backend/Dockerfile for AgentCore Runtime deployment

### 2F: Frontend Foundation

- [X] T033 [FOUND] Create root layout with navigation in frontend/src/app/layout.tsx
- [X] T034 [P] [FOUND] Create StrandsAgent custom provider in frontend/src/lib/strands-provider.ts
- [X] T035 [P] [FOUND] Create Cognito auth utilities (Amplify config, token management, session hooks) in frontend/src/lib/auth.ts
- [X] T036 [FOUND] Create /api/chat streaming route in frontend/src/app/api/chat/route.ts
- [X] T037 [FOUND] Create shared TypeScript types in frontend/src/types/index.ts
- [X] T038 [P] [FOUND] Create Navigation component in frontend/src/components/layout/Navigation.tsx
- [X] T039 [P] [FOUND] Create Header component in frontend/src/components/layout/Header.tsx
- [X] T040 [P] [FOUND] Create Footer component in frontend/src/components/layout/Footer.tsx
- [ ] T032b [FOUND] **Research ai-elements catalogue** - Document available components, identify gaps, justify any custom implementations per Constitution VI gate (output to research.md)

### 2G: Testing Infrastructure

- [X] T041 [P] [FOUND] Configure pytest with fixtures in backend/tests/conftest.py
- [X] T042 [P] [FOUND] Configure Vitest for frontend in frontend/vitest.config.ts
- [X] T043 [P] [FOUND] Configure Playwright E2E in frontend/playwright.config.ts

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 2.5: Cognito Identity Pool & IAM Auth (Priority: NEXT) 🔐

**Purpose**: Enable anonymous frontend access to AgentCore via IAM authentication

**Why this phase**: Per spec clarifications (2025-12-28), anonymous users need AWS credentials to invoke AgentCore. This is a prerequisite for the chat interface to work with the deployed backend.

### 2.5A: Infrastructure - Cognito Identity Pool

- [X] T200 [P] [AUTH] Add Cognito Identity Pool in infrastructure/cognito.tf (unauthenticated access enabled)
- [X] T201 [P] [AUTH] Add Cognito User Pool stub in infrastructure/cognito.tf (deployed but unused for MVP)
- [X] T202 [P] [AUTH] Create IAM role for unauthenticated Identity Pool access with AgentCore invoke permissions
- [X] T203 [AUTH] Update infrastructure/outputs.tf with identity_pool_id, user_pool_id, user_pool_client_id
- [X] T204 [AUTH] Update terraform-aws-agentcore module to accept IAM auth configuration (if needed)

### 2.5B: Frontend - AWS SDK & SigV4 Signing

- [X] T205 [P] [AUTH] Install AWS SDK packages: `@aws-sdk/client-cognito-identity`, `@aws-sdk/credential-providers`
- [X] T206 [AUTH] Create frontend/src/lib/aws-credentials.ts for obtaining anonymous credentials from Identity Pool
- [X] T207 [AUTH] Create frontend/src/lib/sigv4-fetch.ts for SigV4 request signing (implemented in agentcore-transport.ts)
- [X] T208 [AUTH] Update frontend/src/app/api/chat/route.ts to use SigV4-signed requests to AgentCore (browser-direct via useAgentChat hook)

### 2.5C: Backend - IAM Auth Validation

- [X] T209 [AUTH] Update AgentCore runtime configuration to use IAM authentication (remove JWT validation)
- [X] T210 [AUTH] Test IAM-authenticated requests work end-to-end

**Checkpoint**: Anonymous users can invoke AgentCore via SigV4-signed requests

---

## Phase 3: User Story 1 - Conversational Booking Flow (Priority: P1) 🎯 MVP

**Goal**: Users complete full booking through natural conversation with the AI agent

**Independent Test**: Complete end-to-end booking from landing to payment confirmation in < 5 minutes

### 3A: Tests for US1 (Write FIRST, ensure they FAIL)

- [X] T044 [P] [US1] Unit tests for check_availability tool in backend/tests/unit/test_availability.py
- [X] T045 [P] [US1] Unit tests for get_pricing tool in backend/tests/unit/test_pricing.py
- [X] T046 [P] [US1] Unit tests for create_reservation tool in backend/tests/unit/test_reservations.py
- [X] T047 [P] [US1] Integration test for booking flow in backend/tests/integration/test_booking_flow.py
- [X] T047a [P] [US1] Integration test for concurrent booking attempts (first-completed-payment wins) in backend/tests/integration/test_concurrent_booking.py
- [X] T048 [P] [US1] Contract test for /api/chat endpoint in frontend/tests/contract/chat.test.ts
- [X] T049 [US1] E2E test for full booking conversation in frontend/tests/e2e/booking.spec.ts

### 3B: Availability & Pricing Tools (US1)

- [X] T050 [P] [US1] Implement check_availability tool in backend/src/tools/availability.py
- [X] T051 [P] [US1] Implement get_calendar tool in backend/src/tools/availability.py
- [X] T052 [P] [US1] Implement get_pricing tool in backend/src/tools/pricing.py
- [X] T053 [P] [US1] Implement calculate_total tool in backend/src/tools/pricing.py

### 3C: Frontend Chat Interface (US1)

- [X] T062 [US1] Create ChatInterface component with useChat hook in frontend/src/components/agent/ChatInterface.tsx (implemented in ai-elements/conversation.tsx + page.tsx)
- [X] T063 [P] [US1] Create MessageBubble component in frontend/src/components/agent/MessageBubble.tsx (implemented in ai-elements/message.tsx)
- [X] T064 [P] [US1] Create RichContentRenderer for structured responses (delegates to specialized components like PhotoGallery) in frontend/src/components/agent/RichContentRenderer.tsx
- [X] T066 [P] [US1] Create AvailabilityCalendar component in frontend/src/components/agent/AvailabilityCalendar.tsx
- [X] T068 [US1] Create home page with agent as primary interface in frontend/src/app/page.tsx

**Checkpoint**: US1 complete - users can inquire about availability, pricing, and property details through conversation. Run E2E test to validate.

---

## Phase 4: User Story 2 - Availability & Pricing Information (Priority: P2)

**Goal**: Guests explore options before booking (date ranges, seasonal pricing, minimum stays)

**Independent Test**: Ask various availability/pricing questions and verify accurate responses

### 4A: Tests for US2

- [X] T071 [P] [US2] Unit tests for seasonal pricing in backend/tests/unit/test_pricing_seasons.py
- [X] T072 [P] [US2] Unit tests for minimum stay validation in backend/tests/unit/test_minimum_stay.py

### 4B: Enhanced Pricing Tools (US2)

- [X] T073 [US2] Enhance get_pricing to explain seasonal variations in backend/src/tools/pricing.py
- [X] T074 [US2] Add minimum stay tools (check_minimum_stay, get_minimum_stay_info) in backend/src/tools/pricing.py
- [X] T075 [US2] Create pricing seed script with seasonal rates in backend/scripts/seed_data.py

### 4C: Alternative Date Suggestions (US2)

- [X] T076 [US2] Implement suggest_alternative_dates helper in backend/src/services/availability.py (added method to existing AvailabilityService class)
- [X] T077 [US2] Update check_availability to suggest nearby available dates in backend/src/tools/availability.py

**Checkpoint**: US2 complete - guests can explore pricing options and alternatives

---

## Phase 5: User Story 3 - Area Information & Trip Planning (Priority: P3)

**Goal**: Provide local knowledge about Quesada area (golf, beaches, restaurants, activities)

**Independent Test**: Ask area-related questions and verify helpful local information

### 5A: Tests for US3

- [X] T078 [P] [US3] Unit tests for get_area_info tool in backend/tests/unit/test_area_info.py
- [X] T079 [P] [US3] Unit tests for get_recommendations tool in backend/tests/unit/test_recommendations.py

### 5B: Area Info Tools (US3)

- [X] T080 [P] [US3] Implement get_area_info tool in backend/src/tools/area_info.py
- [X] T081 [P] [US3] Implement get_recommendations tool in backend/src/tools/area_info.py
- [X] T082 [US3] Register area info tools with booking_agent in backend/src/agent/booking_agent.py

### 5C: Area Data (US3)

- [X] T083 [US3] Create area info data structure (golf, beaches, restaurants, activities)
- [X] T084 [US3] Seed area info data (S3 or DynamoDB static content)

**Checkpoint**: US3 complete - guests can learn about the Quesada area

---

## Phase 6: User Story 4 - Apartment Details & Amenities (Priority: P4)

**Goal**: Detailed apartment information (bedrooms, amenities, photos)

**Independent Test**: Ask detailed apartment questions and verify comprehensive responses with photos

### 6A: Tests for US4

- [X] T085 [P] [US4] Unit tests for get_property_details tool in backend/tests/unit/test_property.py
- [X] T086 [P] [US4] Unit tests for get_photos tool in backend/tests/unit/test_photos.py

### 6B: Property Tools (US4)

- [X] T087 [P] [US4] Implement get_property_details tool in backend/src/tools/property.py
- [X] T088 [P] [US4] Implement get_photos tool (with category filter) in backend/src/tools/property.py
- [X] T089 [US4] Register property tools with booking_agent in backend/src/agent/booking_agent.py

### 6C: Property Data & Photos (US4)

- [X] T090 [US4] Create property data structure (bedrooms, bathrooms, amenities, rules)
- [ ] T091 [US4] Upload property photos to S3 bucket (requires actual photos - deployment task)
- [X] T092 [P] [US4] Create PhotoGallery component in frontend/src/components/agent/PhotoGallery.tsx

**Checkpoint**: US4 complete - guests can explore apartment details and photos

---

## Phase 7: User Story 6 - Static Information Pages (Priority: P6)

**Goal**: Navigation menu with static pages (Pricing, Location, About, Area Guide, FAQ, Contact)

**Independent Test**: Navigate to each static page and verify content displays without agent

### 8A: Tests for US6

- [X] T102 [US6] E2E tests for static page navigation in frontend/tests/e2e/static-pages.spec.ts

### 8B: Static Pages (US6)

- [X] T103 [P] [US6] Create Pricing page with rate table in frontend/src/app/pricing/page.tsx
- [X] T104 [P] [US6] Create Location page with interactive map in frontend/src/app/location/page.tsx
- [X] T105 [P] [US6] Create About page with photo gallery and amenities in frontend/src/app/about/page.tsx
- [X] T106 [P] [US6] Create Area Guide page in frontend/src/app/area-guide/page.tsx
- [X] T107 [P] [US6] Create FAQ page in frontend/src/app/faq/page.tsx
- [X] T108 [P] [US6] Create Contact page in frontend/src/app/contact/page.tsx

### 8C: Persistent Agent Access (US6 - FR-037)

- [X] T109 [US6] Add persistent agent chat widget to all pages in frontend/src/components/layout/

**Checkpoint**: US6 complete - all static pages available with agent accessible from each

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Improvements affecting multiple user stories

- [X] T110 [P] Add multilingual support (English/Spanish) to system prompt (FR-005)
- [X] T111 [P] Implement error handling with standard error codes from agent-tools.json
- [X] T112 [P] Add structured logging across all tools
- [X] T113 [P] Create API health check endpoint in backend/src/api/health.py
- [ ] T113a [P] Configure CloudWatch dashboard with key metrics (agent response time, error rate) via terraform-aws-agentcore observability outputs (DEFERRED)
- [ ] T113b [P] Configure CloudWatch alarms for critical thresholds (response time > 3s, error rate > 5%, availability table sync failures) (DEFERRED)
- [ ] T113c [P] Configure CloudWatch log retention policy (90 days) per FR-101 (DEFERRED)
- [X] T114 Performance optimization: ensure agent response < 3 seconds (SC-003) - implemented DynamoDB singleton pattern to avoid boto3 re-instantiation overhead (~100-200ms saved per tool call)
- [X] T116 Run quickstart.md validation (all setup commands work) - verified Strands import, TypeScript checks, Taskfile commands, pytest/Vitest tests, uvicorn server startup
- [X] T117 [P] Update CLAUDE.md with final conventions - added DynamoDB singleton pattern, ToolError structured error format documentation
- [X] T120 [P] Create admin data seeding script for pricing/availability updates in backend/scripts/seed_data.py—seeds 2 years of future availability dates per FR-003, 11 seasonal pricing records (2025-Q1 2027), and sample guest records with correct schema

---

## Phase 9: DEFERRED (Post-MVP)

**Purpose**: Features marked DEFERRED in spec.md - to be implemented after MVP launch

**Scope**: Reservations, payments, guest verification, booking management (US5)

### 9A: Reservation Tools (DEFERRED - FR-010 through FR-016)

- [ ] T054 [P] [US1] Implement create_reservation tool in backend/src/tools/reservations.py (DEFERRED)
- [ ] T055 [P] [US1] Implement modify_reservation tool in backend/src/tools/reservations.py (DEFERRED)
- [ ] T056 [US1] Implement cancel_reservation tool in backend/src/tools/reservations.py (DEFERRED)
- [ ] T057 [US1] Register reservation tools with booking_agent in backend/src/agent/booking_agent.py (DEFERRED)

### 9B: Payment Tool (DEFERRED - FR-017)

- [ ] T058 [US1] Unit tests for process_payment tool in backend/tests/unit/test_payment.py (DEFERRED)
- [ ] T059 [US1] Implement process_payment tool (mock) in backend/src/tools/payment.py (DEFERRED)
- [ ] T060 [US1] Register payment tools with booking_agent in backend/src/agent/booking_agent.py (DEFERRED)

### 9C: Guest Verification Tools (DEFERRED - FR-010)

- [ ] T061 [US1] Implement guest verification tools (initiate_verification, verify_code) in backend/src/tools/verification.py (DEFERRED)

### 9D: Deferred UI Components

- [ ] T065 [P] [US1] Create BookingSummaryCard component in frontend/src/components/agent/BookingSummaryCard.tsx (DEFERRED - depends on reservations)
- [ ] T067 [P] [US1] Create VerificationCodeInput component in frontend/src/components/agent/VerificationCodeInput.tsx (DEFERRED)

### 9E: Cognito Passwordless (DEFERRED - email verification for bookings)

- [ ] T069 [FOUND] Create cognito-passwordless module in infrastructure/modules/cognito-passwordless/ (DEFERRED)
- [ ] T070 [FOUND] Add cognito-passwordless module reference in infrastructure/main.tf (DEFERRED)

### 9F: User Story 5 - Booking Management (DEFERRED - Priority: P5)

**Goal**: Guests can retrieve, modify, or cancel existing bookings via conversation

- [ ] T093 [P] [US5] Unit tests for get_guest_info tool in backend/tests/unit/test_guest.py (DEFERRED)
- [ ] T094 [P] [US5] Unit tests for get_reservation tool in backend/tests/unit/test_get_reservation.py (DEFERRED)
- [ ] T095 [US5] Unit tests for modify_reservation edge cases in backend/tests/unit/test_modify_reservation.py (DEFERRED)
- [ ] T096 [US5] Unit tests for cancel_reservation with refund calculation in backend/tests/unit/test_cancel_reservation.py (DEFERRED)
- [ ] T097 [P] [US5] Implement get_guest_info tool in backend/src/tools/guest.py (DEFERRED)
- [ ] T098 [P] [US5] Implement get_reservation tool in backend/src/tools/reservations.py (DEFERRED)
- [ ] T099 [US5] Enhance modify_reservation with date change handling in backend/src/tools/reservations.py (DEFERRED)
- [ ] T100 [US5] Implement cancellation policy in cancel_reservation in backend/src/tools/reservations.py (DEFERRED)
- [ ] T101 [US5] E2E test for booking modification flow in frontend/tests/e2e/modify-booking.spec.ts (DEFERRED)

### 9G: Additional Deferred Items

- [ ] T115 [P] Implement session recovery/reconnection logic in frontend/src/lib/ (FR-008) (DEFERRED - requires conversation persistence)
- [ ] T118 [P] Mobile responsive design for all components (FR-038) (DEFERRED)
- [ ] T119 [P] Create SEO metadata for all static pages (DEFERRED)

**Note**: Phase 9 tasks should only be started after MVP validation and user feedback

---

## Dependencies & Execution Order

### Phase Dependencies

```
Phase 1 (Setup) → Phase 2 (Foundational) → Phase 2.5 (IAM Auth) → Phases 3-7 (User Stories) → Phase 8 (Polish)
                         ↓                        ↓                                                   ↓
                    BLOCKS ALL               ENABLES AgentCore                               Phase 9 (DEFERRED)
                   USER STORIES              INVOCATION                                      (Post-MVP features)
```

**Phase 2.5 Priority**: Per spec clarifications (2025-12-28), Cognito Identity Pool and IAM auth is the **NEXT priority** after foundational work. This enables anonymous users to invoke AgentCore via SigV4-signed requests.

### User Story Dependencies (MVP Scope)

All user stories depend on Phase 2 (Foundational) completion:

| Story | Can Start After | Dependencies on Other Stories |
|-------|-----------------|-------------------------------|
| US1 (P1) | Phase 2 | None - inquiry-only MVP |
| US2 (P2) | Phase 2 | None - enhances pricing from US1 |
| US3 (P3) | Phase 2 | None - independent content |
| US4 (P4) | Phase 2 | None - independent content |
| US6 (P6) | Phase 2 | None - independent pages |
| US5 (P5) | Phase 9 | **DEFERRED** - requires reservation infrastructure |

### Parallel Opportunities

**Phase 2 (Foundational)**: All tasks marked [P] can run in parallel
- DynamoDB tables (T012-T017): 6 parallel
- Pydantic models (T018-T022): 5 parallel
- Core services (T025-T028): 4 parallel
- Frontend layout (T038-T040): 3 parallel

**User Stories**: After Phase 2, multiple stories can proceed in parallel:
- Developer A: US1 (Booking Flow)
- Developer B: US3 + US4 (Content - Area Info + Property)
- Developer C: US6 (Static Pages)

**Within Each Story**: Tests and models marked [P] can run in parallel

---

## Summary

| Phase | Tasks | Parallel Tasks | Key Deliverable |
|-------|-------|----------------|-----------------|
| 1: Setup | 9 | 7 | Project structure + Taskfile + Yarn Berry + Next.js export config |
| 2: Foundational | 37 | 27 | Infrastructure, models, agent skeleton |
| 2.5: IAM Auth | 11 | 4 | Anonymous AgentCore access via Cognito Identity Pool |
| 3: US1 (MVP) | 14 | 6 | Inquiry-only booking via conversation |
| 4: US2 | 7 | 2 | Pricing exploration |
| 5: US3 | 7 | 4 | Area information |
| 6: US4 | 8 | 5 | Apartment details |
| 7: US6 | 8 | 6 | Static pages |
| 8: Polish | 11 | 8 | Quality & performance |
| 9: DEFERRED | 25 | 10 | Reservations, payments, verification (post-MVP) |
| **Total** | **137** | **79** | Full platform |

**MVP Scope**: Phases 1-8 deliver inquiry-only booking functionality (availability, pricing, property details, area info, static pages).

**Post-MVP Scope**: Phase 9 (DEFERRED) contains reservation, payment, and guest verification features for future implementation.

**Operational Constraint**: All Terraform commands MUST be run via `Taskfile.yaml` (never manually). Task T001a sets this up.

**Prerequisite Alerts**:
- Task T006a requires SES domain/email identity verification in AWS console (for future email features).
- Task T007a requires the `static-website` module to exist in `terraform-aws-agentcore/modules/`. This module must be created before frontend deployment.

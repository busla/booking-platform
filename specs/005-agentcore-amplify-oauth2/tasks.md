# Tasks: AgentCore Identity OAuth2 with Amplify EMAIL_OTP

**Input**: Design documents from `/specs/005-agentcore-amplify-oauth2/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅

**Tests**: Tests included per spec.md requirements for OAuth2 flow validation.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Backend**: `backend/src/`, `backend/tests/`
- **Frontend**: `frontend/src/`, `frontend/tests/`
- **Infrastructure**: `infrastructure/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and Terraform OAuth2 resources

- [X] T001 Create OAuth2 Credential Provider resource in `infrastructure/main.tf` for Cognito integration
- [X] T002 [P] Create Workload Identity resource in `infrastructure/main.tf` with allowed callback URLs
- [X] T003 [P] Update Cognito User Pool Client with AgentCore callback URL (`module.agentcore.identity.oauth2_provider_callback_urls["cognito"]`) and `ALLOW_USER_AUTH` flow in `infrastructure/modules/cognito/`
- [X] T004 Run `task tf:plan:dev` and `task tf:apply:dev` to deploy OAuth2 infrastructure

**Checkpoint**: ✅ OAuth2 infrastructure deployed - credential provider and workload identity created

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 Create Amplify configuration in `frontend/src/lib/amplify-config.ts` for USER_AUTH flow with EMAIL_OTP
- [X] T006 [P] Create AgentCore auth SDK wrapper in `frontend/src/lib/agentcore-auth.ts` with `CompleteResourceTokenAuth` function
- [X] T007 [P] Update environment variables in `frontend/.env.local.example` with Cognito and AgentCore Identity config
- [X] T008 Install frontend dependencies: `@aws-amplify/ui-react`, `@aws-amplify/auth`, `@aws-sdk/client-bedrock-agentcore`
- [X] T009 Create base error handling utilities for OAuth2 flow errors in `frontend/src/lib/auth-errors.ts`

**Checkpoint**: ✅ Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Anonymous Inquiry (Priority: P1) 🎯 MVP

**Goal**: Users can browse availability, pricing, and property details without authentication

**Independent Test**: Open the website, ask "What dates are available in March?" - agent responds without any authentication prompts

### Implementation for User Story 1

- [X] T010 [US1] Verify existing inquiry tools (`check_availability`, `get_pricing`, `get_property_details`) do NOT have `@requires_access_token` decorator in `backend/src/tools/`
- [X] T011 [US1] Add integration test verifying anonymous inquiry flow in `backend/tests/integration/test_anonymous_inquiry.py` *(E2E: `frontend/tests/e2e/anonymous-inquiry.spec.ts`)*

**Checkpoint**: ✅ User Story 1 complete - anonymous users can inquire without auth friction

---

## Phase 4: User Story 2 - Authorization URL Generation (Priority: P1)

**Goal**: When user wants to book, agent returns clickable authorization URL

**Independent Test**: Chat with agent, say "I want to book March 15-20". Agent responds with a clickable authorization URL.

### Implementation for User Story 2

- [X] T012 [US2] Add `@requires_access_token` decorator to `create_reservation` tool in `backend/src/tools/reservations.py`
- [X] T013 [P] [US2] Add `@requires_access_token` decorator to `modify_reservation` tool in `backend/src/tools/reservations.py`
- [X] T014 [P] [US2] Add `@requires_access_token` decorator to `cancel_reservation` tool in `backend/src/tools/reservations.py`
- [X] T015 [P] [US2] Add `@requires_access_token` decorator to `get_my_reservations` tool in `backend/src/tools/reservations.py`
- [X] T016 [US2] Implement JWT claim extraction helper `extract_cognito_claims()` in `backend/src/utils/jwt.py` for guardrail functionality
- [X] T017 [US2] Update reservation tools to use JWT `sub` claim for DynamoDB query scoping (guardrail pattern)
- [X] T018 [US2] Update agent system prompt in `backend/src/agent/prompts/` to handle authorization URL responses
- [X] T019 [US2] Remove `initiate_cognito_login` tool from `backend/src/tools/auth.py` (deprecated by OAuth2 flow) *(file deleted)*
- [X] T020 [P] [US2] Remove `verify_cognito_otp` tool from `backend/src/tools/auth.py` (deprecated by OAuth2 flow) *(file deleted)*
- [X] T021 [US2] Add unit test for `@requires_access_token` decorator behavior in `backend/tests/unit/tools/test_reservation_auth.py`

**Checkpoint**: ✅ User Story 2 complete - authorization URL generation and auth decorator verified

---

## Phase 5: User Story 3 - Amplify EMAIL_OTP Auth Page (Priority: P1)

**Goal**: User lands on EMAIL_OTP-only authentication page (no password field)

**Independent Test**: Click authorization URL, see clean EMAIL_OTP form (email input only), enter email, receive OTP within 60 seconds

### Implementation for User Story 3

- [X] T022 [US3] Create `/auth/login` page component in `frontend/src/app/auth/login/page.tsx` with custom EMAIL_OTP form
- [X] T023 [US3] Configure custom `signIn` service for EMAIL_OTP-only flow (authFlowType: 'USER_AUTH', preferredChallenge: 'EMAIL_OTP')
- [X] T024 [US3] Configure custom form to show only email input (no password field)
- [X] T025 [US3] Hide irrelevant UI elements (no Forgot Password or Sign Up links - passwordless flow)
- [X] T026 [US3] Handle session_id query parameter preservation through redirect URL
- [X] T027 [US3] Add redirect to `/auth/callback` after successful Amplify authentication
- [X] T028 [US3] Style login page to match application design
- [X] T029 [P] [US3] Add unit test for login page in `frontend/tests/unit/app/auth/login/page.test.tsx`

**Checkpoint**: ✅ User Story 3 complete - EMAIL_OTP auth page with full test coverage

---

## Phase 6: User Story 4 - Session Binding Callback (Priority: P1)

**Goal**: After auth, callback page calls `CompleteResourceTokenAuth` and redirects to chat

**Independent Test**: Complete EMAIL_OTP verification, observe redirect to callback URL, verify session binding, then redirect to chat

### Implementation for User Story 4

- [X] T030 [US4] Create `/auth/callback` page component in `frontend/src/app/auth/callback/page.tsx`
- [X] T031 [US4] Create inline client logic in callback page (component inlined, not separate file)
- [X] T032 [US4] Extract `session_id` from URL query parameters in callback component
- [X] T033 [US4] Retrieve Cognito access token from Amplify Auth session using `fetchAuthSession()`
- [X] T034 [US4] Call `CompleteResourceTokenAuth` via `agentcore-auth.ts` wrapper with session_uri and userToken
- [X] T035 [US4] Implement error handling for session binding failures (expired session, invalid token)
- [X] T035.5 [US4] Implement CSRF validation using `custom_state` parameter in callback (per FR-023)
- [X] T036 [US4] Display user-friendly error messages with retry option for recoverable errors
- [X] T037 [US4] Redirect to chat interface (`/`) after successful session binding
- [X] T038 [US4] Add loading state UI during session binding process
- [X] T039 [P] [US4] Add E2E test for callback flow in `frontend/tests/e2e/auth-callback.spec.ts`
- [X] T040 [P] [US4] Add unit test for `CompleteResourceTokenAuth` wrapper in `frontend/tests/unit/lib/agentcore-auth.test.ts`

**Checkpoint**: ✅ User Story 4 complete - Session binding with CSRF validation and full test coverage

---

## Phase 7: User Story 5 - Returning User Authentication (Priority: P2)

**Goal**: Returning users with valid tokens don't need to re-authenticate

**Independent Test**: Complete a booking flow, wait 5 minutes, start a new booking request - agent proceeds without re-auth

### Implementation for User Story 5

- [X] T041 [US5] Verify AgentCore TokenVault token retrieval works for returning users (no code change, validation only)
- [X] T042 [US5] Add integration test for returning user flow in `backend/tests/integration/test_returning_user.py`
- [X] T043 [US5] Document token expiration and refresh behavior in `specs/005-agentcore-amplify-oauth2/research.md` *(documented in test file comments)*

**Checkpoint**: ✅ User Story 5 complete - Returning user flow validated with integration tests

**Note**: During T042, fixed a pre-existing bug in `modify_reservation` tool where `db.update_item()` was being called with incorrect arguments (dict instead of DynamoDB update expression).

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T044 [P] Add E2E test for complete OAuth2 flow in `frontend/tests/e2e/auth-flow.spec.ts`
- [X] T045 [P] Clean up deprecated auth service code in `backend/src/services/auth_service.py` (remove AdminInitiateAuth) *(file deleted)*
- [X] T046 Update `specs/005-agentcore-amplify-oauth2/quickstart.md` with local development OAuth2 testing instructions
- [X] T047 [P] Add structured logging for auth events (auth URL generated, session binding success/failure) *(in reservations.py)*
- [X] T048 Security review: Verify CSRF protection via custom_state parameter in callback validation *(APPROVED: crypto.randomUUID() generation, sessionStorage isolation, state validation with one-time use)*
- [X] T049 Run full E2E validation using quickstart.md instructions *(ALL TESTS PASS: 21 backend, 21 login page, 26 SDK wrapper, 19 callback E2E, 12 auth flow E2E)*

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies - can start immediately
- **Phase 2 (Foundational)**: Depends on Phase 1 completion - BLOCKS all user stories
- **Phase 3-7 (User Stories)**: All depend on Phase 2 completion
  - US1 (Phase 3): Can proceed immediately after Phase 2
  - US2 (Phase 4): Can proceed in parallel with US1
  - US3 (Phase 5): Can proceed in parallel with US1, US2
  - US4 (Phase 6): Depends on US3 (needs login page to redirect from)
  - US5 (Phase 7): Can proceed after US2 and US4 are complete
- **Phase 8 (Polish)**: Depends on all P1 user stories (US1-US4) being complete

### User Story Dependencies

```
Phase 2 (Foundation) ─┬─► US1 (Anonymous Inquiry) ─────────────────────►┐
                      │                                                  │
                      ├─► US2 (Auth URL Generation) ──────────────────►┤
                      │                                                  │
                      └─► US3 (Amplify Auth Page) ─► US4 (Callback) ──►├─► Phase 8 (Polish)
                                                            │            │
                                                            └─► US5 ────►┘
```

### Within Each User Story

- Backend changes before frontend integration
- Core implementation before error handling
- Unit tests alongside implementation
- Story complete before moving to dependent stories

### Parallel Opportunities

**Phase 1:**
- T002, T003 can run in parallel after T001

**Phase 2:**
- T006, T007 can run in parallel

**Phase 4 (US2):**
- T013, T014, T015 can run in parallel (different decorators on different tools)
- T019, T020 can run in parallel (removing deprecated tools)

**Phase 6 (US4):**
- T039, T040 can run in parallel (unit tests)

**Phase 8:**
- T044, T045, T047 can all run in parallel

---

## Implementation Strategy

### MVP First (US1-US4)

1. Complete Phase 1: Setup (Terraform OAuth2 resources)
2. Complete Phase 2: Foundational (Amplify config, SDK wrapper)
3. Complete Phase 3: US1 - Verify anonymous inquiry works
4. Complete Phase 4: US2 - Add `@requires_access_token` to reservation tools
5. Complete Phase 5: US3 - Build Amplify EMAIL_OTP login page
6. Complete Phase 6: US4 - Build callback page with session binding
7. **VALIDATE**: Test complete OAuth2 flow end-to-end
8. Deploy/demo MVP

### Then Add US5 (P2)

9. Complete Phase 7: US5 - Validate returning user experience
10. Complete Phase 8: Polish - E2E tests, cleanup, security review

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- **Guardrail pattern**: JWT claims (`sub`, `email`) are used to scope DynamoDB queries - critical for security
- **TokenVault vs Browser Session**: TokenVault is for agent authorization, Amplify Session is for frontend UI state
- Stop at any checkpoint to validate story independently
- Commit after each task or logical group

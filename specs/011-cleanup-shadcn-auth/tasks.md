# Tasks: Frontend Cleanup and Consistency

**Input**: Design documents from `/specs/011-cleanup-shadcn-auth/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/

**Tests**: Tests are run via existing test suites (`task test`). No new test files required - this is a refactoring feature.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Install required shadcn components and verify baseline

- [x] T001 Run `task test` to establish baseline - all tests must pass before changes; also run `task frontend:build && du -sh frontend/out/` to capture baseline bundle size (SC-009)
- [x] T002 [P] Install shadcn Alert component: `cd frontend && npx shadcn@latest add alert`
- [x] T003 [P] Install shadcn Badge component: `cd frontend && npx shadcn@latest add badge`
- [x] T004 Verify shadcn installation: `ls frontend/src/components/ui/` includes alert.tsx and badge.tsx

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Infrastructure changes that enable terminology rename; enforce module dependency patterns (FR-024, FR-025)

**CRITICAL**: DynamoDB table rename must complete before backend model changes. Table names must be passed via module outputs, never hardcoded.

- [x] T005 Audit `infrastructure/` for hardcoded DynamoDB table names - document any violations of FR-024
- [x] T006 Update `infrastructure/modules/dynamodb/main.tf`: rename module "guests" to module "customers", change hash_key to "customer_id"
- [x] T007 Update `infrastructure/modules/dynamodb/outputs.tf`: ensure table name and ARN are exported as outputs
- [x] T008 Update `infrastructure/modules/cognito/main.tf`: add schema attributes for phone_number and name (standard attributes)
- [x] T009 Update consuming modules (Lambda, API Gateway) to receive table names via input variables instead of hardcoded strings
- [x] T010 Run `task tf:plan:dev` and review changes (should show guests table destroy, customers table create; no hardcoded table names)
- [x] T011 Run `task tf:apply:dev` to apply infrastructure changes
- [x] T012 Verify SC-014: `grep -r "booking-.*-customers\|booking-.*-guests" infrastructure/ | grep -v "outputs.tf\|dynamodb/main.tf"` returns 0 results (no hardcoded table names outside DynamoDB module)

**Checkpoint**: Infrastructure ready - DynamoDB customers table and Cognito attributes configured; table names passed via outputs

---

## Phase 3: User Story 1 - Developer Maintains Consistent Codebase (Priority: P1)

**Goal**: Ensure no conflicting type definitions, consistent terminology, no dead code

**Independent Test**: Run `grep -r "type AuthStep" frontend/src/` - should return only 1 file

### Implementation for User Story 1

- [x] T013 [US1] Rename type in `frontend/src/app/auth/login/page.tsx`: change `type AuthStep` to `type LoginStep`
- [x] T014 [US1] Update all references in login/page.tsx: `AuthStep` to `LoginStep` (state declarations, type annotations)
- [x] T015 [US1] Verify no type conflicts: `grep -r "type AuthStep" frontend/src/` returns only `useAuthenticatedUser.ts`
- [x] T016 [US1] Run `task frontend:test` to verify no regressions

**Checkpoint**: Type conflict resolved - single canonical AuthStep definition exists

---

## Phase 4: User Story 2 - Consistent Authentication User Experience (Priority: P1)

**Goal**: All auth error displays use shadcn Alert component with theme-aware styling

**Independent Test**: Navigate to login page, trigger error states, verify consistent styling

### Implementation for User Story 2

- [x] T017 [US2] Migrate `frontend/src/components/booking/AuthErrorBoundary.tsx`: replace hardcoded `bg-red-50`, `text-red-800` with shadcn Alert `variant="destructive"`
- [x] T018 [US2] Update AuthErrorBoundary: replace custom button with shadcn Button component
- [x] T019 [US2] Import Alert, AlertDescription, AlertTitle from `@/components/ui/alert` and AlertCircle from `lucide-react`
- [x] T020 [US2] Run `task frontend:test` to verify AuthErrorBoundary tests pass
- [x] T021 [US2] Verify no hardcoded error colors: `grep -r "bg-red-50\|text-red-800" frontend/src/components/` returns 0 results

**Checkpoint**: Auth error handling uses consistent shadcn styling

---

## Phase 5: User Story 6 - Complete Customer Profile Storage (Priority: P1)

**Goal**: All customer profile fields stored in both Cognito and DynamoDB

**Independent Test**: Complete customer details form, verify fields in both Cognito and DynamoDB

### Backend Implementation for User Story 6

- [x] T022 [P] [US6] Rename `backend/shared/src/shared/models/guest.py` to `customer.py`
- [x] T023 [P] [US6] Rename `backend/shared/src/shared/tools/guest.py` to `customer.py`
- [x] T024 [US6] Update `backend/shared/src/shared/models/customer.py`: rename class Guest to Customer, guest_id to customer_id
- [x] T025 [US6] Update `backend/shared/src/shared/tools/customer.py`: rename all guest references to customer
- [x] T026 [US6] Update `backend/shared/src/shared/services/dynamodb.py`: use table name from environment variable (set via Terraform output), not hardcoded string
- [x] T027 [US6] Update `backend/shared/src/shared/services/cognito.py`: add adminUpdateUserAttributes to save phone_number and name
- [x] T028 [US6] Merge `backend/api/src/api/routes/guests.py` functionality into `routes/customers.py`
- [x] T029 [US6] Delete `backend/api/src/api/routes/guests.py` after merge
- [x] T030 [US6] Update all backend imports: search for `from shared.models.guest` and `from shared.tools.guest`
- [x] T031 [US6] Run `task backend:test` to verify all tests pass

### Frontend Implementation for User Story 6

- [x] T032 [US6] Start backend dev server: `task backend:dev &`
- [x] T033 [US6] Regenerate API client: `cd frontend && task frontend:generate:api`
- [x] T034 [US6] Stop backend dev server
- [x] T035 [P] [US6] Rename `frontend/src/components/booking/GuestDetailsForm.tsx` to `CustomerDetailsForm.tsx`
- [x] T036 [US6] Update CustomerDetailsForm.tsx: rename component and all internal references
- [x] T037 [US6] Update all frontend imports: search for `GuestDetailsForm` and update to `CustomerDetailsForm`
- [x] T038 [US6] Update frontend types if needed: search for `Guest` type references
- [x] T039 [US6] Run `task frontend:test` to verify all tests pass

**Checkpoint**: Full guest→customer rename complete, profile data flows to Cognito + DynamoDB

---

## Phase 6: User Story 3 - Clean Component Library (Priority: P2)

**Goal**: All cards, alerts, badges use shadcn components consistently

**Independent Test**: Visual inspection of BookingSummaryCard status badges

### Implementation for User Story 3

- [x] T040 [US3] Migrate `frontend/src/components/agent/BookingSummaryCard.tsx`: replace `getStatusColor()` with shadcn Badge
- [x] T041 [US3] Import Badge from `@/components/ui/badge`
- [x] T042 [US3] Create `getStatusVariant()` helper: confirmed/paid→default, pending→secondary, cancelled→destructive, default→outline
- [x] T043 [US3] Replace status span elements with `<Badge variant={getStatusVariant(status)}>{status}</Badge>`
- [x] T044 [US3] Remove old `getStatusColor()` function if no longer used
- [x] T045 [US3] Run `task frontend:test` to verify BookingSummaryCard tests pass

**Checkpoint**: All status badges use shadcn Badge with theme-aware variants

---

## Phase 7: User Story 4 - Removed Dead Code (Priority: P2)

**Goal**: No dead code, unused exports, or deprecated patterns in codebase

**Independent Test**: `grep -r "PhotoGallery" frontend/src/` returns 0 results

### Implementation for User Story 4

- [x] T046 [US4] Verify PhotoGallery.tsx is still unused: `grep -r "import.*PhotoGallery" frontend/src/` returns empty
- [x] T047 [US4] Delete dead code: `rm frontend/src/components/agent/PhotoGallery.tsx`
- [x] T048 [US4] Verify yet-another-react-lightbox is STILL used: `grep -r "yet-another-react-lightbox" frontend/src/` returns `/gallery/page.tsx`
- [x] T049 [US4] Run `npx depcheck` in frontend to check for unused dependencies; remove any findings
- [x] T050 [US4] Verify FR-009: `grep -r "amplifyAuthServices\|amplifyFormFields" frontend/src/` returns 0 results (confirm already removed)
- [x] T051 [US4] Audit FR-011 placeholders: `grep -rn "XXX\|TKTK\|TODO.*placeholder\|+34 XXX" frontend/src/` - document or fix any findings
- [x] T052 [US4] Run `task frontend:test` to verify no regressions from deletion

**Checkpoint**: Dead code removed, actively-used dependencies retained

---

## Phase 8: User Story 5 - Standardized Styling Patterns (Priority: P3)

**Goal**: All components use cn() utility and theme-aware color variants

**Independent Test**: `grep -r "bg-gray-50" frontend/src/app/` returns 0 results in loading/auth components

### Next.js Routing Implementation for User Story 5

- [x] T053 [US5] Create route group directory: `mkdir -p frontend/src/app/\(auth\)/login frontend/src/app/\(auth\)/callback`
- [x] T054 [US5] Move login page: `mv frontend/src/app/auth/login/page.tsx frontend/src/app/\(auth\)/login/page.tsx`
- [x] T055 [US5] Move callback page: `mv frontend/src/app/auth/callback/page.tsx frontend/src/app/\(auth\)/callback/page.tsx`
- [x] T056 [US5] Remove old auth directory: `rmdir frontend/src/app/auth/login frontend/src/app/auth/callback frontend/src/app/auth`
- [x] T057 [P] [US5] Create `frontend/src/app/(auth)/layout.tsx` with shared auth page layout using bg-background
- [x] T058 [P] [US5] Create `frontend/src/app/(auth)/loading.tsx` using shadcn Skeleton component
- [x] T059 [P] [US5] Create `frontend/src/app/(auth)/error.tsx` using shadcn Alert with variant="destructive"
- [x] T060 [US5] Update inline Suspense fallbacks in `(auth)/login/page.tsx`: replace bg-gray-50 with bg-background
- [x] T061 [US5] Update inline Suspense fallbacks in `(auth)/callback/page.tsx`: replace bg-gray-50 with bg-muted
- [x] T062 [US5] Verify no hardcoded gray colors: `grep -r "bg-gray-50" frontend/src/app/` returns 0 results
- [x] T063 [US5] Run `task frontend:dev` and navigate to /login to verify route still works

**Checkpoint**: Auth routes organized with Next.js conventions, theme-aware styling throughout

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Final verification across all user stories

- [x] T064 Run full test suite: `task test`
- [x] T065 Build frontend and capture bundle size: `task frontend:build && du -sh frontend/out/` - record size for comparison
- [x] T066 Compare bundle size to baseline from T001: verify no increase (SC-009)
- [x] T067 Run E2E tests: `task frontend:test:e2e` to verify auth flow
- [x] T068 Verify all success criteria from spec.md:
  - [x] `grep -r "type AuthStep" frontend/src/` returns only 1 file (SC-001)
  - [x] `grep -r "bg-red-50\|text-red-800" frontend/src/components/` returns 0 (SC-002, SC-007)
  - [x] `grep -r "guest_id" backend/shared/src/` returns 0 (SC-011)
  - [x] `grep -r "GuestDetailsForm" frontend/src/` returns 0 (SC-011)
  - [x] `ls frontend/src/app/\(auth\)/` shows layout.tsx, loading.tsx, error.tsx (SC-012)
  - [x] `grep -r "bg-gray-50" frontend/src/app/` returns 0 in auth components (SC-013)
  - [x] `grep -r "booking-.*-customers\|booking-.*-guests" infrastructure/ | grep -v "outputs.tf\|dynamodb/main.tf"` returns 0 (SC-014)
- [x] T069 Run quickstart.md validation: execute verification checklist

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup - BLOCKS terminology rename; establishes module output pattern
- **User Story 1 (Phase 3)**: Can start after Setup (independent of infrastructure)
- **User Story 2 (Phase 4)**: Can start after Setup (independent of infrastructure)
- **User Story 6 (Phase 5)**: REQUIRES Foundational (Phase 2) complete - depends on customers table
- **User Story 3 (Phase 6)**: Can start after Setup (independent)
- **User Story 4 (Phase 7)**: Can start after Setup (independent)
- **User Story 5 (Phase 8)**: Depends on US1 (type rename affects moved files)
- **Polish (Phase 9)**: Depends on all user stories complete

### Parallel Opportunities

```
Phase 1 (Setup):           T002, T003 can run in parallel
Phase 2 (Foundational):    Sequential (terraform changes); T005-T007 can run in parallel
Phase 3 (US1):             Can run parallel with US2, US3, US4
Phase 4 (US2):             Can run parallel with US1, US3, US4
Phase 5 (US6):             T022, T023 can run in parallel; T035 parallel with backend
Phase 6 (US3):             Can run parallel with US1, US2, US4
Phase 7 (US4):             Can run parallel with US1, US2, US3
Phase 8 (US5):             T057, T058, T059 can run in parallel
```

### Critical Path

```
T001 → T002/T003 → T004 → T005-T012 (Infrastructure + table naming) → T022-T039 (US6) → T064-T069
```

The terminology rename (US6) is the critical path as it requires infrastructure changes first, and infrastructure now includes verifying table name outputs (FR-024, FR-025).

---

## Implementation Strategy

### MVP First (P1 Stories Only)

1. Complete Phase 1: Setup (shadcn components)
2. Complete Phase 2: Foundational (infrastructure + table output verification)
3. Complete Phase 3: US1 (type consolidation)
4. Complete Phase 4: US2 (auth error styling)
5. Complete Phase 5: US6 (terminology rename + Cognito storage)
6. **STOP and VALIDATE**: Run `task test` + manual E2E testing
7. Deploy/demo if ready

### Full Implementation

Continue with P2 stories (US3, US4) and P3 story (US5) after MVP validation.

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- PhotoGallery.tsx deletion (US4) is independent and can happen early
- Route group creation (US5) should happen after type rename (US1) to avoid double-handling page.tsx
- yet-another-react-lightbox is KEPT - it powers /gallery/ route (do NOT remove)
- All `task test` runs verify no regressions before proceeding
- **NEW (FR-024, FR-025)**: DynamoDB table names MUST be passed via Terraform module outputs, never hardcoded in consuming modules
- **NEW (SC-014)**: Verification added to confirm no hardcoded table name strings outside DynamoDB module

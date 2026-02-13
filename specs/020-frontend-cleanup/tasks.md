# Tasks: Frontend Cleanup & Test Consolidation

**Feature**: 020-frontend-cleanup
**Generated**: 2026-01-06
**Source**: [spec.md](./spec.md), [plan.md](./plan.md), [research.md](./research.md)

## Task Overview

| Phase | Tasks | Priority | Dependencies |
|-------|-------|----------|--------------|
| 0 - Prerequisites | 2 | P0 | None |
| 1 - US1+US2 (Core Cleanup) | 8 | P1 | Phase 0 |
| 2 - US3 (Test Organization) | 3 | P2 | Phase 1 |
| 3 - US4 (Infrastructure) | 3 | P3 | Phase 2 |
| 4 - Polish | 2 | P1 | Phase 3 |

**Total Tasks**: 18

---

## Phase 0: Prerequisites

*Verify infrastructure before making destructive changes.*

- [x] **T001** [P0] Verify OTP infrastructure is functional
  - Run: `cd frontend && yarn playwright test otp-retrieval.spec.ts`
  - **Expected**: Test passes, confirming DynamoDB `verification_codes` table is accessible
  - **File**: `frontend/tests/e2e/otp-retrieval.spec.ts`
  - **Blocks**: T005, T006, T007 (cannot remove PASSWORD_AUTH until OTP flow is verified)

- [x] **T002** [P0] Run baseline test suite and document current state
  - Run: `cd frontend && yarn test && yarn test:e2e --list`
  - **Expected**: Document which tests pass/fail before cleanup
  - **Purpose**: Establishes baseline to measure improvement

---

## Phase 1: US1 + US2 - Core Cleanup (P1)

*Developer Runs Tests with Confidence + Codebase Free of Debug Artifacts*

### Debug File Removal (FR-001, SC-004)

- [x] **T003** [P1] [US2] Delete debug-header-length.spec.ts
  - **Action**: `rm frontend/tests/e2e/debug-header-length.spec.ts`
  - **File**: `frontend/tests/e2e/debug-header-length.spec.ts` (83 lines)
  - **Verification**: `ls frontend/tests/e2e/debug-* 2>/dev/null || echo "Clean"`

- [x] **T004** [P1] [US2] Delete debug-real-jwt.spec.ts
  - **Action**: `rm frontend/tests/e2e/debug-real-jwt.spec.ts`
  - **File**: `frontend/tests/e2e/debug-real-jwt.spec.ts` (178 lines)
  - **Verification**: `ls frontend/tests/e2e/debug-* 2>/dev/null || echo "Clean"`

### PASSWORD_AUTH Removal (FR-010, FR-011, SC-009)

- [x] **T005** [P1] [US2] Remove SSM_PASSWORD_PARAM and TEST_USER_PASSWORD from auth.fixture.ts
  - **File**: `frontend/tests/e2e/fixtures/auth.fixture.ts`
  - **Lines to remove**: 53 (`SSM_PASSWORD_PARAM`), 57 (`TEST_USER_PASSWORD`)
  - **Depends on**: T001 (OTP verification)

- [x] **T006** [P1] [US2] Remove password loading logic from loadCredentials()
  - **File**: `frontend/tests/e2e/fixtures/auth.fixture.ts`
  - **Lines to remove**: 104, 112-114, 123 (password loading from env/SSM)
  - **Depends on**: T005

- [x] **T007** [P1] [US2] Remove authenticateWithPassword() function
  - **File**: `frontend/tests/e2e/fixtures/auth.fixture.ts`
  - **Lines to remove**: 251-291 (entire function using USER_PASSWORD_AUTH)
  - **Depends on**: T006

- [x] **T008** [P1] [US2] Remove password mode detection and branching
  - **File**: `frontend/tests/e2e/fixtures/auth.fixture.ts`
  - **Lines to remove/modify**: 497, 599-600, 610 (conditional password logic)
  - **Verification**: `grep -c 'PASSWORD_AUTH\|USER_PASSWORD_AUTH' frontend/tests/e2e/fixtures/auth.fixture.ts` should return 0
  - **Depends on**: T007

### Placeholder and TODO Cleanup (FR-002, FR-006, SC-005)

- [x] **T009** [P1] [US2] Replace placeholder phone number
  - **File**: `frontend/src/app/contact/page.tsx:36`
  - **Change**: `'+34 XXX XXX XXX'` → `'+3547798217'`
  - **Verification**: `grep -c 'XXX XXX' frontend/src/app/contact/page.tsx` should return 0

- [x] **T010** [P1] [US2] Remove outdated TODO comment
  - **File**: `frontend/src/hooks/usePricing.ts:94`
  - **Change**: Remove or update `// TODO: Replace with actual API endpoint when backend is ready`
  - **Reason**: API endpoint at `/api/pricing` is functional

---

## Phase 2: US3 - Test Organization (P2)

*Clear Test Organization with No Duplication*

### Auth Test Consolidation (FR-003, SC-006)

- [x] **T011** [P2] [US3] Review auth test files for overlap
  - **Files to analyze**:
    - `frontend/tests/e2e/auth.spec.ts` (551 lines)
    - `frontend/tests/e2e/auth-step.spec.ts` (447 lines)
    - `frontend/tests/e2e/auth-flow.spec.ts` (572 lines)
    - `frontend/tests/e2e/auth-callback.spec.ts` (508 lines)
  - **Action**: Document test coverage overlap in research.md or inline comments
  - **Target**: Identify tests that can be consolidated (SC-006: ≤3 auth test files)
  - **Depends on**: T008 (PASSWORD_AUTH removed)

- [x] **T012** [P2] [US3] Consolidate overlapping auth tests
  - **Action**: Merge duplicate test coverage, keeping most comprehensive tests
  - **Depends on**: T011

### Documentation (FR-007, SC-008)

- [x] **T013** [P2] [US3] Create test organization README
  - **File**: `frontend/tests/e2e/README.md` (CREATE)
  - **Content**: Test directory structure, localhost vs live strategy, where to add new tests
  - **Depends on**: T012

---

## Phase 3: US4 - Maintainable Infrastructure (P3)

*Maintainable Test Infrastructure*

### Helper Extraction (FR-008, SC-007)

- [x] **T014** [P3] [US4] Extract calendar interaction helper
  - **File**: `frontend/tests/e2e/utils/page-objects/calendar.ts` (CREATE)
  - **Pattern**: Date selection in booking form (used >3 times across tests)
  - **Target**: SC-007 requires at least 3 reusable helpers

- [x] **T015** [P3] [US4] Extract OTP input helper
  - **File**: `frontend/tests/e2e/utils/page-objects/otp-input.ts` (CREATE)
  - **Pattern**: 6-digit code entry flow (used >3 times across tests)

- [x] **T016** [P3] [US4] Extract form submission helper
  - **File**: `frontend/tests/e2e/utils/page-objects/booking-form.ts` (CREATE)
  - **Pattern**: Multi-step form navigation (used >3 times across tests)

---

## Phase 4: Polish

*Final verification and documentation*

### Test Verification (FR-004, FR-005, SC-001, SC-002, SC-003)

- [x] **T017** [P1] Run full test suite - localhost
  - **Commands**:
    ```bash
    cd frontend
    yarn test                    # Unit tests (SC-001)
    yarn test:e2e                # E2E localhost (SC-002)
    ```
  - **Expected**: 100% pass rate
  - **Depends on**: All previous tasks

- [x] **T018** [P1] Run full test suite - live site
  - **Commands**:
    ```bash
    cd frontend
    E2E_BASE_URL=https://booking.levy.apro.work yarn playwright test integration/
    ```
  - **Expected**: 100% pass rate (SC-003)
  - **Depends on**: T017

---

## Dependency Graph

```
T001 (Verify OTP) ─────┐
                       │
T002 (Baseline) ───────┼───► T003, T004 (Delete debug files)
                       │
                       └───► T005 ──► T006 ──► T007 ──► T008 (PASSWORD_AUTH removal chain)
                                                           │
T009, T010 (Placeholder/TODO) ────────────────────────────┼───► T011 ──► T012 ──► T013
                                                           │              │
                                                           │              └───► T014, T015, T016
                                                           │                           │
                                                           └───────────────────────────┼───► T017 ──► T018
```

## Parallel Execution Opportunities

Tasks that can be executed in parallel:

1. **After T001+T002**: T003, T004, T009, T010 (independent cleanup tasks)
2. **After T008**: T011 can start immediately
3. **After T012**: T013, T014, T015, T016 (documentation and helpers)

## Validation Checklist

Run these commands after completing all tasks:

```bash
# SC-004: No debug files
ls frontend/tests/e2e/debug-* 2>/dev/null || echo "✓ SC-004 PASS"

# SC-005: No placeholder phone
[ $(grep -c 'XXX XXX' frontend/src/app/contact/page.tsx) -eq 0 ] && echo "✓ SC-005 PASS"

# SC-009: No PASSWORD_AUTH code
[ $(grep -c 'PASSWORD_AUTH' frontend/tests/e2e/fixtures/auth.fixture.ts) -eq 0 ] && echo "✓ SC-009 PASS"

# SC-001: Unit tests pass
cd frontend && yarn test && echo "✓ SC-001 PASS"

# SC-002: E2E localhost tests pass
cd frontend && yarn test:e2e && echo "✓ SC-002 PASS"

# SC-003: E2E live tests pass
cd frontend && E2E_BASE_URL=https://booking.levy.apro.work yarn playwright test integration/ && echo "✓ SC-003 PASS"

# SC-006: Auth test file count
[ $(ls frontend/tests/e2e/auth*.spec.ts | wc -l) -le 3 ] && echo "✓ SC-006 PASS"

# SC-007: Helper functions exist
[ -f frontend/tests/e2e/utils/page-objects/calendar.ts ] && \
[ -f frontend/tests/e2e/utils/page-objects/otp-input.ts ] && \
[ -f frontend/tests/e2e/utils/page-objects/booking-form.ts ] && echo "✓ SC-007 PASS"

# SC-008: README exists
[ -f frontend/tests/e2e/README.md ] && echo "✓ SC-008 PASS"
```

## Notes

- **Risk Mitigation**: T001 verifies OTP infrastructure before removing PASSWORD_AUTH to prevent test suite breakage
- **Rollback**: All changes are file deletions or edits; git provides easy rollback via `git checkout -- frontend/`
- **CI Consideration**: T017/T018 validation ensures CI will pass after PR merge

# Research: Frontend Cleanup & Test Consolidation

**Feature**: 020-frontend-cleanup
**Date**: 2026-01-06
**Scope**: Frontend E2E test cleanup, debug file removal, auth consolidation

## Executive Summary

This research documents the current state of the frontend codebase, specifically focused on:
1. Debug files requiring deletion
2. PASSWORD_AUTH code requiring removal
3. Placeholder values requiring real data
4. Test organization opportunities

**Key Finding**: The frontend E2E test infrastructure has grown organically with 7,521 lines across 20 files. Two debug investigation files and one legacy authentication approach need removal to maintain code quality.

---

## Inventory: Files Requiring Changes

### 1. Debug Files (DELETE)

| File | Lines | Purpose | Action |
|------|-------|---------|--------|
| `frontend/tests/e2e/debug-header-length.spec.ts` | 83 | Investigation: JWT header length vs WAF | DELETE |
| `frontend/tests/e2e/debug-real-jwt.spec.ts` | 178 | Investigation: Real JWT vs SDK behavior | DELETE |

Both files contain `test.skip()` - they're not running and were created for debugging authorization issues on Jan 5, 2026.

### 2. PASSWORD_AUTH Code (REMOVE from auth.fixture.ts)

Location: `frontend/tests/e2e/fixtures/auth.fixture.ts` (635 lines)

**Code to Remove:**

```typescript
// Lines 53, 57: SSM parameter and variable for password
const SSM_PASSWORD_PARAM = '/booking/e2e/test-user-password'
let TEST_USER_PASSWORD = ''

// Lines 104, 112-114, 123: Password loading logic
TEST_USER_PASSWORD = process.env.E2E_TEST_USER_PASSWORD || ''
if (!TEST_USER_PASSWORD) {
  TEST_USER_PASSWORD = (await getSSMParameter(SSM_PASSWORD_PARAM, true)) || ''
}

// Lines 251-291: authenticateWithPassword() function
async function authenticateWithPassword(): Promise<{...}>
// Uses AuthFlow: 'USER_PASSWORD_AUTH'

// Lines 497, 599-600, 610: Password mode detection and branching
} else if (TEST_USER_PASSWORD) {
const headless = !!TEST_USER_PASSWORD
console.log(`Mode: ${TEST_USER_PASSWORD ? 'Password (CI)' : 'EMAIL_OTP (manual)'}`)
```

**Impact**: After removal, the fixture will only support OTP-based authentication via:
1. Stored state reuse (`.auth-state/user.json`)
2. EMAIL_OTP UI flow (for initial setup or manual testing)

### 3. Placeholder Values (REPLACE)

| File | Line | Current Value | New Value |
|------|------|---------------|-----------|
| `frontend/src/app/contact/page.tsx` | 36 | `'+34 XXX XXX XXX'` | `'+3547798217'` |

### 4. Outdated TODO Comments (UPDATE/REMOVE)

| File | Line | Comment | Action |
|------|------|---------|--------|
| `frontend/src/hooks/usePricing.ts` | 94 | `// TODO: Replace with actual API endpoint when backend is ready` | REMOVE - API is working |

---

## Inventory: Test File Structure

### Root-Level Spec Files (13 files)

| File | Lines | Domain | Status |
|------|-------|--------|--------|
| auth.spec.ts | 551 | Authentication | KEEP - core localStorage tests |
| auth-step.spec.ts | 447 | Booking auth step | KEEP - TDD tests for T011 |
| auth-flow.spec.ts | 572 | Token delivery SSE | KEEP - T021 token flow |
| auth-callback.spec.ts | 508 | OAuth2 callback | KEEP - edge case tests |
| booking.spec.ts | 366 | Booking form | KEEP - review for overlap |
| direct-booking.spec.ts | 529 | Non-agent booking | KEEP |
| payment-flow.spec.ts | 1,379 | Stripe Checkout | KEEP - comprehensive |
| routing.spec.ts | 398 | Navigation | KEEP |
| static-pages.spec.ts | 345 | Static content | KEEP |
| anonymous-inquiry.spec.ts | 201 | Guest flow | KEEP |
| otp-retrieval.spec.ts | 146 | OTP Lambda validation | KEEP - spec 019 |
| debug-header-length.spec.ts | 83 | DEBUG | **DELETE** |
| debug-real-jwt.spec.ts | 178 | DEBUG | **DELETE** |

### Integration Tests (4 files)

| File | Lines | Purpose |
|------|-------|---------|
| booking-flow-with-otp.spec.ts | 443 | Real OTP + API flow |
| booking.spec.ts | 317 | Integration booking |
| live-payment-flow.spec.ts | 626 | Real Stripe flow |
| reservation-flow.spec.ts | 432 | Full reservation |

### Fixtures & Utilities (3 files)

| File | Lines | Purpose |
|------|-------|---------|
| fixtures/auth.fixture.ts | 635 | Auth provider (needs cleanup) |
| utils/otp-helper.ts | 159 | OTP DynamoDB retrieval |
| scripts/setup-test-user.ts | 237 | Test user setup CLI |

---

## Auth Testing Strategy Analysis

### Current State

The auth.fixture.ts provides THREE authentication strategies:

1. **Stored State** - Reuses `.auth-state/user.json` if valid tokens exist
2. **PASSWORD_AUTH** - Cognito USER_PASSWORD_AUTH flow (legacy, CI-focused)
3. **EMAIL_OTP UI** - Manual OTP entry in browser (slow, but standard)

### Target State (after cleanup)

Only TWO strategies should remain:

1. **Stored State** - Reuses `.auth-state/user.json` if valid tokens exist
2. **EMAIL_OTP Programmatic** - Uses otp-helper.ts to retrieve OTP from DynamoDB

The otp-helper.ts already provides:
- `getOtpForEmail()` - Polls DynamoDB for OTP (5s timeout)
- `generateTestEmail()` - Creates valid test email patterns
- `clearOtpForEmail()` - Cleans up after tests

### Files Using Password Authentication

Based on grep analysis, PASSWORD_AUTH references exist in:
1. `frontend/tests/e2e/fixtures/auth.fixture.ts` - **PRIMARY TARGET**
2. `frontend/tests/e2e/scripts/setup-test-user.ts` - Uses password for user setup (may need review)

---

## Test Organization Recommendations

### Localhost vs Live Tests

Currently there's no clear separation documented. Recommended structure:

```
frontend/tests/e2e/
├── localhost/           # Mocked tests (fast, no real APIs)
│   ├── auth/
│   ├── booking/
│   └── ...
├── integration/         # Real API tests (existing)
│   └── ...
├── fixtures/
├── utils/
│   └── page-objects/    # NEW: Extract common patterns
└── README.md            # NEW: Document test organization
```

### Common Patterns to Extract

Based on test file analysis, these patterns repeat >3 times:

1. **Calendar interaction** - Date selection in booking form
2. **OTP input** - 6-digit code entry flow
3. **Form submission** - Multi-step form navigation
4. **Auth state injection** - localStorage token setup

---

## Dependencies

### AWS Infrastructure (existing)

- Cognito User Pool: `eu-west-1_VEgg3Z7oI`
- Cognito Client ID: `7n7e6gq90rcr6dlg7pn1jrd15l`
- DynamoDB table: `verification_codes` (OTP storage)
- Lambda trigger: Custom Message trigger for OTP interception

### SSM Parameters (cleanup needed)

Currently referenced:
- `/booking/e2e/test-user-email` - KEEP
- `/booking/e2e/test-user-password` - CAN BE REMOVED after fixture cleanup

### NPM Dependencies (no changes)

- @playwright/test
- @aws-sdk/client-cognito-identity-provider
- @aws-sdk/client-dynamodb
- @aws-sdk/client-ssm

---

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Removing PASSWORD_AUTH breaks CI | High | Ensure OTP flow works in CI before removing |
| Auth fixture changes break tests | Medium | Run full test suite after each change |
| Consolidation loses test coverage | Medium | Review coverage before merging files |

---

## Open Questions Resolved

| Question | Resolution |
|----------|------------|
| Auth handling in E2E tests | Remove PASSWORD_AUTH, use OTP via Lambda+DynamoDB |
| Contact phone placeholder | Replace with +3547798217 |
| TODO in usePricing.ts | Remove - API endpoint is working |

---

## Next Steps

1. Delete debug files (FR-001, SC-004)
2. Replace placeholder phone (FR-002, SC-005)
3. Remove PASSWORD_AUTH code from auth.fixture.ts (FR-010, FR-011, SC-009)
4. Remove outdated TODO comment (FR-006)
5. Run all tests to validate (SC-001, SC-002, SC-003)
6. Extract common test helpers (FR-008, SC-007)
7. Document test organization (FR-007, SC-008)

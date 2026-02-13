# Quickstart: Frontend Cleanup & Test Consolidation

**Feature**: 020-frontend-cleanup
**Date**: 2026-01-06

## Prerequisites

- Node.js 18+ and Yarn Berry installed
- AWS credentials configured (for E2E test OTP retrieval)
- Frontend dependencies installed: `task frontend:install`

## Implementation Order

This cleanup should be executed in the following order to minimize risk:

### Phase 1: Safe Deletions (No Dependencies)

```bash
# Delete debug files
rm frontend/tests/e2e/debug-header-length.spec.ts
rm frontend/tests/e2e/debug-real-jwt.spec.ts

# Verify tests still run
cd frontend && yarn test:e2e --list
```

### Phase 2: Value Replacements

**File**: `frontend/src/app/contact/page.tsx:36`
```diff
- { name: 'Property Manager', number: '+34 XXX XXX XXX', description: 'Urgent property issues' },
+ { name: 'Property Manager', number: '+3547798217', description: 'Urgent property issues' },
```

**File**: `frontend/src/hooks/usePricing.ts:94`
```diff
- // TODO: Replace with actual API endpoint when backend is ready
+ // Pricing fetched from backend API
```

### Phase 3: Auth Fixture Cleanup

**File**: `frontend/tests/e2e/fixtures/auth.fixture.ts`

This is the most complex change. Remove:
1. SSM_PASSWORD_PARAM constant
2. TEST_USER_PASSWORD variable
3. Password loading in loadCredentials()
4. authenticateWithPassword() function (entire function)
5. All branching logic based on TEST_USER_PASSWORD

**Before removing**, ensure the OTP-based flow works:

```bash
# Run OTP retrieval test to verify infrastructure
cd frontend && yarn playwright test otp-retrieval.spec.ts

# Run an integration test that uses OTP
cd frontend && yarn playwright test integration/booking-flow-with-otp.spec.ts
```

### Phase 4: Verification

```bash
# Run all unit tests
cd frontend && yarn test

# Run localhost E2E tests
cd frontend && yarn test:e2e

# Run live site integration tests
cd frontend && E2E_BASE_URL=https://booking.levy.apro.work yarn playwright test integration/
```

## Test Commands Reference

| Command | Description |
|---------|-------------|
| `yarn test` | Run Vitest unit tests |
| `yarn test:e2e` | Run Playwright E2E tests (localhost) |
| `yarn playwright test --ui` | Interactive test runner |
| `yarn playwright test <file>` | Run specific test file |
| `E2E_BASE_URL=https://... yarn playwright test integration/` | Run against live site |

## Validation Checklist

- [ ] Zero files with "debug" prefix: `ls frontend/tests/e2e/debug-* 2>/dev/null || echo "Clean"`
- [ ] No PASSWORD_AUTH in fixture: `grep -c PASSWORD_AUTH frontend/tests/e2e/fixtures/auth.fixture.ts` (should be 0)
- [ ] No placeholder phone: `grep -c "XXX XXX" frontend/src/app/contact/page.tsx` (should be 0)
- [ ] Unit tests pass: `cd frontend && yarn test`
- [ ] E2E localhost tests pass: `cd frontend && yarn test:e2e`
- [ ] E2E live tests pass: against booking.levy.apro.work

## Rollback Plan

If issues arise, git provides easy rollback:

```bash
# View changes before committing
git diff

# If something breaks, revert individual files
git checkout -- frontend/tests/e2e/fixtures/auth.fixture.ts

# Or revert all changes
git checkout -- frontend/
```

## Common Issues

### OTP Retrieval Timeout

If `getOtpForEmail()` times out:
1. Check DynamoDB table `verification_codes` exists
2. Check Lambda trigger is enabled on Cognito
3. Verify AWS credentials have DynamoDB read access

### Auth Fixture Fails After PASSWORD_AUTH Removal

1. Delete stored state: `rm -rf frontend/tests/e2e/.auth-state/`
2. Run with debug output: `DEBUG=pw:api yarn playwright test auth.spec.ts`
3. Check Cognito console for user status

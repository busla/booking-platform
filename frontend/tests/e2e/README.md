# E2E Test Directory

This directory contains Playwright end-to-end tests for the booking application.

## Directory Structure

```
tests/e2e/
├── fixtures/                  # Test fixtures (authentication, etc.)
│   └── auth.fixture.ts        # Cognito authentication fixture
├── integration/               # Live site integration tests
│   └── *.spec.ts              # Tests that run against booking.levy.apro.work
├── utils/                     # Test utilities and helpers
│   └── otp-helper.ts          # OTP retrieval from DynamoDB
├── .auth-state/               # Stored auth state (gitignored)
├── *.spec.ts                  # Test files (localhost tests)
└── README.md                  # This file
```

## Test Files

| File | Description | Target |
|------|-------------|--------|
| `auth.spec.ts` | Core auth primitives: session, tokens, validation, accessibility | localhost |
| `auth-callback.spec.ts` | OAuth2 callback + SSE token delivery flows | localhost |
| `auth-step.spec.ts` | Booking form auth step UI component | localhost |
| `anonymous-inquiry.spec.ts` | Unauthenticated user flows | localhost |
| `booking.spec.ts` | Conversation flow and chat interface | localhost |
| `direct-booking.spec.ts` | Direct booking flow (date selection → payment) | localhost |
| `otp-retrieval.spec.ts` | OTP retrieval from DynamoDB verification_codes | localhost |
| `payment-flow.spec.ts` | Stripe payment integration | localhost |
| `routing.spec.ts` | App routing and navigation | localhost |
| `static-pages.spec.ts` | Static content pages (pricing, about, FAQ) | localhost |

## Running Tests

### Localhost Tests (Development)

```bash
# Run all localhost tests
yarn test:e2e

# Run specific test file
yarn playwright test auth.spec.ts

# Run with UI mode (interactive)
yarn playwright test --ui
```

### Live Site Tests (Integration)

```bash
# Run integration tests against live site
E2E_BASE_URL=https://booking.levy.apro.work yarn playwright test integration/

# Or use the full integration command
yarn test:e2e:live
```

## Authentication in Tests

Tests requiring authentication use the `auth.fixture.ts`:

```typescript
import { test } from './fixtures/auth.fixture'

test('authenticated test', async ({ authenticatedPage }) => {
  // authenticatedPage has valid Cognito session
  await authenticatedPage.goto('/profile')
})
```

### Authentication Modes

1. **Stored state reuse**: Fastest, reads from `.auth-state/user.json`
2. **EMAIL_OTP flow**: Manual code entry for fresh authentication

To set up fresh auth state:
```bash
npx ts-node tests/e2e/fixtures/auth.fixture.ts
```

## OTP Retrieval

For tests that need OTP codes, use the OTP helper:

```typescript
import { retrieveOTP, generateTestEmail } from './utils/otp-helper'

const email = generateTestEmail()  // booking-test-{timestamp}@test.levy.apro.work
const otp = await retrieveOTP(email, { maxWaitMs: 30000 })
```

The OTP helper reads from the DynamoDB `verification_codes` table.

## Adding New Tests

1. **Localhost tests**: Create `feature-name.spec.ts` in this directory
2. **Live site tests**: Create in `integration/` subdirectory
3. **Shared utilities**: Add to `utils/` directory
4. **Auth-dependent tests**: Import from `fixtures/auth.fixture.ts`

## Test Organization Philosophy

- **auth.spec.ts**: Low-level auth primitives (type guards, storage, validation)
- **auth-callback.spec.ts**: Post-authentication flows (OAuth2 + SSE token delivery)
- **auth-step.spec.ts**: UI component for the booking auth step
- **Other files**: Feature-specific tests (booking, payment, routing)

Each file focuses on a single concern to keep tests maintainable and easy to debug.

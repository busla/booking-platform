# Implementation Plan: Frontend Cleanup & Test Consolidation

**Branch**: `020-frontend-cleanup` | **Date**: 2026-01-06 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/020-frontend-cleanup/spec.md`

## Summary

This feature focuses on cleaning up the frontend codebase to remove debug artifacts, consolidate duplicate E2E tests, and ensure all tests pass. The primary technical work involves:

1. Removing debug test files (`debug-*.spec.ts`)
2. Removing legacy PASSWORD_AUTH test code and using only OTP-based authentication
3. Replacing placeholder contact phone with real number (+3547798217)
4. Consolidating overlapping auth test files
5. Extracting common test patterns into reusable helpers
6. Ensuring 100% test pass rate for both localhost and live environments

## Technical Context

**Language/Version**: TypeScript 5.x (strict mode), Next.js 14+ (App Router)
**Primary Dependencies**: Playwright (E2E), Vitest (unit), @aws-sdk/client-dynamodb (OTP retrieval)
**Storage**: DynamoDB `verification_codes` table (read-only for OTP retrieval in tests)
**Testing**: Playwright for E2E tests, Vitest for unit tests
**Target Platform**: Web (localhost:3000 + booking.levy.apro.work)
**Project Type**: Web application (frontend-only changes in this feature)
**Performance Goals**: N/A (cleanup feature, no new functionality)
**Constraints**: Tests must pass in CI without manual intervention, OTP retrieval timeout <30s
**Scale/Scope**: ~15 test files affected, ~3 source files modified

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Test-First Development | N/A | This is a cleanup feature; we're fixing existing tests, not adding new functionality requiring TDD |
| II. Simplicity & YAGNI | ✅ PASS | Removing debug files and dead code aligns perfectly with this principle |
| III. Type Safety | ✅ PASS | No type changes required; existing TypeScript strict mode maintained |
| IV. Observability | N/A | No new services or logging changes |
| V. Incremental Delivery | ✅ PASS | Can deliver in stages: (1) delete debug files, (2) remove PASSWORD_AUTH, (3) consolidate tests |
| VI. Technology Stack | N/A | No new technologies; using existing Playwright/Vitest stack |
| - shadcn/ui First | N/A | No UI component changes |
| - Frontend API Integration | N/A | No API client changes |

**Gate Status**: ✅ PASS - All applicable constitution principles satisfied

### Post-Design Re-evaluation (Phase 1 Complete)

After completing research and design phases, the Constitution Check remains valid:

- **No new abstractions introduced** - only removing code
- **No new dependencies** - using existing Playwright, Vitest, AWS SDK
- **OTP-based auth aligns with existing infrastructure** - spec 019 already deployed
- **Incremental delivery confirmed** - can ship debug deletion, phone fix, and auth cleanup independently

## Project Structure

### Documentation (this feature)

```text
specs/020-frontend-cleanup/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command) - MINIMAL for cleanup feature
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command) - N/A for cleanup feature
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
frontend/
├── src/
│   ├── app/
│   │   └── contact/
│   │       └── page.tsx          # Phone number placeholder fix
│   ├── hooks/
│   │   └── usePricing.ts         # TODO comment cleanup
│   └── lib/
│       └── auth.ts               # No cleanup needed (verified clean)
└── tests/
    └── e2e/
        ├── fixtures/
        │   └── auth.fixture.ts   # Remove PASSWORD_AUTH code
        ├── utils/
        │   ├── otp-helper.ts     # Keep (OTP retrieval - good)
        │   └── page-objects/     # Extract common patterns here
        ├── auth.spec.ts          # Consolidate auth tests
        ├── auth-flow.spec.ts     # Review for consolidation
        ├── auth-callback.spec.ts # Review for consolidation
        ├── debug-*.spec.ts       # DELETE these files
        └── README.md             # Document test organization
```

**Structure Decision**: This feature operates within the existing frontend structure. No new directories are created except potentially `utils/page-objects/` for extracted helpers. The focus is on file deletion, modification, and consolidation rather than structural changes.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No violations - this cleanup feature aligns with all constitution principles, particularly "Simplicity & YAGNI" through code deletion and consolidation.

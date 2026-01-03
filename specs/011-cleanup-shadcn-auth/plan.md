# Implementation Plan: Frontend Cleanup and Consistency

**Branch**: `011-cleanup-shadcn-auth` | **Date**: 2026-01-03 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/011-cleanup-shadcn-auth/spec.md`

## Summary

This feature focuses on frontend cleanup and consistency by:
1. Replacing custom UI components with shadcn equivalents (Alert, Badge, Dialog)
2. Resolving conflicting `AuthStep` type definitions
3. Removing dead code and unused dependencies
4. Standardizing "customer" terminology (renaming from "guest")
5. Ensuring all customer profile fields are stored in DynamoDB

## Technical Context

**Language/Version**: TypeScript 5.7+ (frontend), Python 3.13+ (backend)
**Primary Dependencies**: Next.js 14+, shadcn/ui (Radix primitives), Tailwind CSS, AWS Amplify, FastAPI, Pydantic v2
**Storage**: AWS DynamoDB (`customers` table - renamed from `guests`), AWS Cognito (all profile fields: email, phone_number, name)
**Testing**: Vitest (frontend unit), Playwright (E2E), pytest (backend)
**Target Platform**: Web (static export via Next.js)
**Project Type**: Web application (frontend + backend)
**Performance Goals**: No bundle size increase (ideally smaller due to dead code removal)
**Constraints**: Zero regression in existing authentication flows, shadcn components must match current UX
**Scale/Scope**: ~15 component files affected, ~25 backend files for terminology rename

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence |
|-----------|--------|----------|
| **I. Test-First Development** | PASS | Existing test suite covers auth flows; new component tests will be written before migration |
| **II. Simplicity & YAGNI** | PASS | This feature removes unused code and consolidates patterns - directly aligned |
| **III. Type Safety** | PASS | Resolves conflicting `AuthStep` types; maintains strict TypeScript |
| **IV. Observability** | N/A | No new observability requirements for UI refactoring |
| **V. Incremental Delivery** | PASS | Each user story is independently testable and deployable |
| **VI. Technology Stack - UI Components** | PASS | Feature aligns with constitution v1.3.0 requirement to prefer shadcn/ui |
| **VI. Technology Stack - API Integration** | N/A | No new API endpoints; existing generated client continues to work |

**Pre-Design Gate Result**: PASS - All applicable principles satisfied or aligned.

### Post-Design Re-Evaluation

| Principle | Status | Evidence |
|-----------|--------|----------|
| **I. Test-First Development** | PASS | Plan includes running test suites before/after each change; quickstart has verification steps |
| **II. Simplicity & YAGNI** | PASS | Removes dead code (`yet-another-react-lightbox`), consolidates patterns; no new abstractions added |
| **III. Type Safety** | PASS | Resolves type conflicts (AuthStep → LoginStep rename); Cognito user attributes use standard types |
| **IV. Observability** | N/A | UI refactoring - no new observability requirements |
| **V. Incremental Delivery** | PASS | Each phase is independently testable; can merge shadcn migrations separately from terminology rename |
| **VI. Technology Stack - UI Components** | PASS | Directly implements constitution requirement: shadcn Alert, Badge, Dialog replace custom implementations |
| **VI. Technology Stack - API Integration** | PASS | OpenAPI client regeneration included in quickstart Step 8 |

**Post-Design Gate Result**: PASS - Design aligns with all constitution principles. New clarifications (Cognito storage, duplicate verification) are additive and don't violate any principles.

## Project Structure

### Documentation (this feature)

```text
specs/011-cleanup-shadcn-auth/
├── spec.md              # Feature specification
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output (customer entity changes)
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (API route changes)
│   └── api-changes.md   # Summary of endpoint renames
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
frontend/
├── src/
│   ├── app/
│   │   ├── (auth)/                     # Auth route group (NEW)
│   │   │   ├── layout.tsx              # Shared auth page layout
│   │   │   ├── loading.tsx             # Route-level loading UI
│   │   │   ├── error.tsx               # Route-level error boundary
│   │   │   ├── login/page.tsx          # Login page (moved from auth/)
│   │   │   └── callback/page.tsx       # OAuth callback (moved from auth/)
│   │   └── auth/login/page.tsx         # AuthStep type to rename (BEFORE move)
│   ├── components/
│   │   ├── agent/
│   │   │   ├── BookingSummaryCard.tsx  # Replace with shadcn Badge
│   │   │   └── PhotoGallery.tsx        # DELETE (dead code - zero imports)
│   │   ├── booking/
│   │   │   ├── AuthErrorBoundary.tsx   # Replace with shadcn Alert + Button
│   │   │   └── GuestDetailsForm.tsx    # Rename to CustomerDetailsForm
│   │   └── ui/
│   │       ├── alert.tsx               # NEW: Install shadcn Alert
│   │       └── badge.tsx               # NEW: Install shadcn Badge
│   ├── hooks/
│   │   └── useAuthenticatedUser.ts     # Primary AuthStep definition
│   └── types/
│       └── index.ts                    # Guest → Customer type renames
└── tests/
    └── unit/
        └── components/                 # New tests for migrated components

backend/
├── shared/
│   └── src/shared/
│       ├── models/
│       │   └── guest.py → customer.py  # Rename file and classes
│       ├── services/
│       │   └── dynamodb.py             # Update table references
│       └── tools/
│           └── guest.py → customer.py  # Rename file and functions
├── api/
│   └── src/api/
│       └── routes/
│           └── guests.py               # Merge into customers.py
└── tests/                              # Update all guest → customer refs

infrastructure/
└── modules/dynamodb/main.tf            # Rename guests table to customers
```

**Structure Decision**: Existing web application structure maintained. Changes are refactoring within existing directories - no new directories needed.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | No violations | All changes align with constitution principles |

## Implementation Approach

### Phase 1: Component Migrations (Frontend)

1. **Install missing shadcn components**
   - `npx shadcn@latest add alert` - For AuthErrorBoundary replacement
   - `npx shadcn@latest add badge` - For BookingSummaryCard status indicators

2. **Migrate AuthErrorBoundary** (FR-004, FR-005)
   - Replace hardcoded `bg-red-50`, `text-red-800` with shadcn Alert `variant="destructive"`
   - Replace custom button with shadcn Button

3. **Migrate BookingSummaryCard** (FR-006)
   - Replace `getStatusColor()` helper with shadcn Badge variants
   - Map: confirmed→default, pending→secondary, cancelled→destructive

4. ~~**Migrate PhotoGallery lightbox** (FR-007)~~ **REMOVED**: PhotoGallery.tsx is dead code (zero imports) - delete instead of migrate

### Phase 2: Type Consolidation (Frontend)

1. **Resolve AuthStep conflict** (FR-001)
   - Keep `AuthStep` in `useAuthenticatedUser.ts` as canonical definition
   - Rename login page type to `LoginStep` (values: 'email' | 'otp' | 'success' | 'error')

### Phase 3: Terminology Rename (Full-Stack)

1. **Frontend renames** (FR-017, FR-019)
   - `GuestDetailsForm.tsx` → `CustomerDetailsForm.tsx`
   - `GuestCountSelector.tsx` → stays (refers to booking guest count, not entity)
   - Update all type imports: `Guest` → `Customer`

2. **Backend renames** (FR-017)
   - `models/guest.py` → `models/customer.py`
   - `tools/guest.py` → `tools/customer.py`
   - Merge `routes/guests.py` into `routes/customers.py`
   - Update all `guest_id` → `customer_id`

3. **Infrastructure changes** (FR-018)
   - Rename DynamoDB table module: `guests` → `customers`
   - Update GSI names and references

### Phase 4: Dead Code Removal

1. **Verify and remove unused code** (FR-009, FR-010, FR-011)
   - Confirm `amplifyAuthServices` and `amplifyFormFields` are not used anywhere
   - **KEEP** `yet-another-react-lightbox` - it IS used by `/gallery/page.tsx` (standalone gallery with thumbnails/zoom)
   - **DELETE** `PhotoGallery.tsx` - verified DEAD CODE (zero imports anywhere in codebase)
   - Remove any placeholder data in production code

### Phase 5: Next.js Routing Best Practices (Frontend)

1. **Create auth route group** (FR-020)
   - Create `frontend/src/app/(auth)/` route group directory
   - Move `auth/login/page.tsx` to `(auth)/login/page.tsx`
   - Move `auth/callback/page.tsx` to `(auth)/callback/page.tsx`
   - Create shared layout `(auth)/layout.tsx` for consistent auth page styling

2. **Add loading.tsx convention files** (FR-021)
   - Create `(auth)/loading.tsx` using shadcn Skeleton component
   - Ensure spinner/loading patterns use theme-aware classes (not `bg-gray-50`)

3. **Add error.tsx convention files** (FR-022)
   - Create `(auth)/error.tsx` using shadcn Alert with `variant="destructive"`
   - Include error recovery UI with shadcn Button

4. **Update inline Suspense fallbacks** (FR-023)
   - Replace `bg-gray-50`, `text-gray-500` in `LoginLoading()` and `CallbackLoading()` with theme-aware classes
   - Use CSS variables or Tailwind theme colors for consistency

### Phase 6: Customer Data Storage (Backend + Infrastructure)

1. **Configure Cognito to store all profile fields** (FR-015)
   - Update Terraform Cognito User Pool schema to include `phone_number` and `name` attributes
   - These are standard Cognito attributes (not custom) for best compatibility

2. **Update backend to save profile to Cognito** (FR-014)
   - Modify customer registration/update to call `adminUpdateUserAttributes` on Cognito
   - Store `email` (username), `phone_number`, `name` in Cognito user attributes
   - Continue storing to DynamoDB `customers` table for booking queries

3. **Update frontend to read profile from Cognito** (FR-016)
   - Modify `useAuthenticatedUser` hook to read profile from Cognito session attributes
   - This avoids DynamoDB lookup, improving UI rendering performance
   - Enables future SMS login via Cognito `phone_number` attribute

## Dependencies

### Component Dependencies
- shadcn Alert depends on: `@radix-ui/react-alert-dialog` (may need installation)
- shadcn Badge: No additional dependencies (uses cva)

### Migration Order
1. Install shadcn components first
2. Migrate components (can be parallel)
3. Type consolidation (after component migrations)
4. Terminology rename (requires coordination frontend + backend)
5. Dead code removal (last - verify nothing breaks)

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| shadcn component behavior differs from current | Low | Medium | Test each component individually; keep custom behavior if essential |
| Terminology rename breaks API contract | Medium | High | Update OpenAPI spec first; regenerate client; test all endpoints |
| Dead code removal breaks functionality | Low | High | Run full test suite before/after; manual E2E testing |
| DynamoDB table rename causes issues | Low | Medium | Greenfield project - data loss acceptable; use Terraform destroy/create |

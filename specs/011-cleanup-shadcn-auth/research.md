# Research: Frontend Cleanup and Consistency

**Feature**: 011-cleanup-shadcn-auth
**Date**: 2026-01-03
**Purpose**: Resolve all NEEDS CLARIFICATION items and document technology decisions

## Research Areas

### 1. shadcn Alert Component for AuthErrorBoundary

**Decision**: Use shadcn Alert with `variant="destructive"` for error display

**Rationale**:
- shadcn Alert provides accessible error states out of the box
- `variant="destructive"` maps to theme-aware destructive colors
- Includes `AlertTitle` and `AlertDescription` for structured error messages
- Already uses Radix primitives which are installed in the project

**Alternatives Considered**:
- Keep custom implementation: Rejected - hardcoded colors violate FR-012
- Use Radix Alert directly: Rejected - shadcn provides better defaults and matches project patterns

**Implementation Pattern**:
```tsx
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { AlertCircle } from 'lucide-react'

<Alert variant="destructive">
  <AlertCircle className="h-4 w-4" />
  <AlertTitle>Something went wrong</AlertTitle>
  <AlertDescription>
    We encountered an unexpected error. Please try again.
  </AlertDescription>
</Alert>
```

### 2. shadcn Badge Component for Status Indicators

**Decision**: Use shadcn Badge with semantic variants for booking status

**Rationale**:
- Badge provides consistent styling for status indicators
- Variants map to semantic meaning: `default`, `secondary`, `destructive`, `outline`
- Eliminates need for `getStatusColor()` helper with hardcoded Tailwind classes

**Status Mapping**:
| Current Status | Badge Variant | Visual Result |
|----------------|---------------|---------------|
| confirmed | `default` | Primary color (success-like) |
| paid | `default` | Primary color |
| pending | `secondary` | Muted background |
| cancelled | `destructive` | Red/error styling |
| refunded | `outline` | Border only, subtle |

**Alternatives Considered**:
- Custom Badge component: Rejected - reinvents what shadcn provides
- CSS variables for colors: Partial - still requires custom component wrapper

**Implementation Pattern**:
```tsx
import { Badge } from '@/components/ui/badge'

function getStatusVariant(status: string): 'default' | 'secondary' | 'destructive' | 'outline' {
  switch (status.toLowerCase()) {
    case 'confirmed':
    case 'paid':
      return 'default'
    case 'pending':
      return 'secondary'
    case 'cancelled':
      return 'destructive'
    default:
      return 'outline'
  }
}

<Badge variant={getStatusVariant(reservationStatus)}>
  {reservationStatus}
</Badge>
```

### 3. ~~shadcn Dialog for PhotoGallery Lightbox~~ **OBSOLETE - PhotoGallery is Dead Code**

**Decision**: ~~Use shadcn Dialog for lightbox modal~~ **DELETE PhotoGallery.tsx entirely**

**Verification Results** (2026-01-03):
```bash
# Search for imports of PhotoGallery - ZERO results
grep -r "import.*PhotoGallery" frontend/src/
grep -r "from.*PhotoGallery" frontend/src/

# Only matches found were WITHIN PhotoGallery.tsx itself (self-references)
grep -r "PhotoGallery" frontend/src/
# Result: Only frontend/src/components/agent/PhotoGallery.tsx
```

**Conclusion**: `PhotoGallery.tsx` has zero imports anywhere in the codebase. It is dead code and should be deleted, not migrated.

**Note**: The `/gallery/page.tsx` route uses `yet-another-react-lightbox` (a completely different implementation) - that code remains unchanged and the library is KEPT.

### 4. AuthStep Type Consolidation

**Pre-Removal Analysis** (CRITICAL: per clarification - verify BEFORE removing):

| Aspect | `useAuthenticatedUser.ts` | `login/page.tsx` |
|--------|---------------------------|------------------|
| **Purpose** | Session-level auth state machine | UI form step navigation |
| **Values** | anonymous, sending_otp, awaiting_otp, verifying, authenticated | email, otp, success, error |
| **Scope** | Global (exported, used in hooks) | Local (page-only, not exported) |
| **Behavior** | Controls auth flow across app | Controls single page UI flow |
| **Tests** | Covered by auth hook tests | Covered by login page tests |

**Verdict**: BOTH implementations are CORRECT for their respective purposes. These are NOT duplicates - they represent different concepts that unfortunately share the same name.

**Decision**: Keep two separate types with distinct names

**Rationale**:
- The two `AuthStep` types serve different purposes:
  - `useAuthenticatedUser.ts`: Session-level auth state (anonymous → authenticated)
  - `login/page.tsx`: UI form step (email → otp → success)
- Merging them would create a confusing union with semantically different values
- Renaming clarifies intent and prevents import conflicts

**Naming Strategy**:
| Location | Current Name | New Name | Values |
|----------|--------------|----------|--------|
| `useAuthenticatedUser.ts` | `AuthStep` | `AuthStep` (keep) | anonymous, sending_otp, awaiting_otp, verifying, authenticated |
| `login/page.tsx` | `AuthStep` | `LoginStep` | email, otp, success, error |

**Alternatives Considered**:
- Merge into single type: Rejected - semantically different concepts
- Use discriminated union: Rejected - unnecessary complexity for local state
- Export from shared types: Rejected - login page type is page-local
- Remove one implementation: **REJECTED** - per analysis above, BOTH are needed

### 5. Guest → Customer Terminology Migration

**Decision**: Full rename across codebase with DynamoDB table recreation

**Rationale**:
- "Customer" is the correct business term for someone making a booking
- "Guest" is ambiguous (could mean "unauthenticated user" or "booking guest count")
- Greenfield project allows clean break without migration concerns
- Terraform can destroy/create table cleanly

**Scope of Changes**:

| Layer | Files Affected | Change Type |
|-------|----------------|-------------|
| Frontend Types | `types.gen.ts` (auto-generated) | Regenerate after backend |
| Frontend Components | `GuestDetailsForm.tsx` | Rename file + component |
| Backend Models | `models/guest.py` | Rename to `customer.py` |
| Backend Tools | `tools/guest.py` | Rename to `customer.py` |
| Backend Routes | `routes/guests.py` | Merge into `customers.py` |
| Infrastructure | `modules/dynamodb/main.tf` | Rename module |

**Migration Order**:
1. Infrastructure (Terraform apply creates new `customers` table)
2. Backend models/tools/routes
3. Regenerate OpenAPI spec
4. Frontend regenerate API client
5. Frontend component renames

**Alternatives Considered**:
- Keep "guest" terminology: Rejected - creates ongoing confusion
- Gradual migration with aliases: Rejected - unnecessary for greenfield

### 6. Dead Code Verification

**Decision**: Remove confirmed dead code; KEEP `yet-another-react-lightbox` (actively used)

**Findings**:

| Item | Status | Evidence | Action |
|------|--------|----------|--------|
| `amplifyAuthServices` | NOT FOUND | Grep returned no matches | N/A (already removed) |
| `amplifyFormFields` | NOT FOUND | Grep returned no matches | N/A (already removed) |
| `yet-another-react-lightbox` | **USED** | `/gallery/page.tsx` imports and uses it | **KEEP** - do NOT remove |

**Verification Commands Run**:
```bash
# These returned no matches
grep -r "amplifyAuthServices" frontend/src/
grep -r "amplifyFormFields" frontend/src/

# This FOUND a match - library IS used
grep -r "yet-another-react-lightbox" frontend/src/
# Result: frontend/src/app/gallery/page.tsx
```

**Package Dependency Analysis**:
- `yet-another-react-lightbox` v3.28.0 is in dependencies
- **USED BY**: `frontend/src/app/gallery/page.tsx` (standalone gallery route)
  - Uses Thumbnails and Zoom plugins
  - Full-featured lightbox with keyboard navigation, thumbnails, zoom
- **NOT USED BY**: `PhotoGallery.tsx` (agent chat component - uses custom lightbox)
- **KEEP** the library - it powers the `/gallery/` route

**Two Lightbox Implementations - BOTH CORRECT FOR THEIR PURPOSES**:

| Component | Location | Implementation | Purpose | Action |
|-----------|----------|----------------|---------|--------|
| Gallery Page | `/gallery/page.tsx` | `yet-another-react-lightbox` | Standalone gallery with thumbnails, zoom | KEEP as-is |
| PhotoGallery | `components/agent/PhotoGallery.tsx` | Custom `<div>` modal | ~~Agent chat inline photos~~ **DEAD CODE** | **DELETE** (zero imports) |

**Updated Rationale** (2026-01-03):
1. `/gallery/` route needs advanced features (thumbnails, zoom) that shadcn Dialog doesn't provide - **KEEP**
2. `PhotoGallery.tsx` has **zero imports** anywhere in the codebase - it is dead code - **DELETE**

### 7. Customer Profile Storage

**Decision**: Store all three fields in BOTH Cognito AND DynamoDB

**Rationale** (per user clarification):
1. **Improved UI rendering**: Profile fields in Cognito session attributes = no DynamoDB lookup needed
2. **Future SMS login**: `phone_number` attribute in Cognito enables SMS_OTP auth flow
3. **Dual storage**: DynamoDB still needed for booking queries and relationships

**Updated Storage Model**:

| Field | Cognito Storage | DynamoDB Storage | Purpose |
|-------|-----------------|------------------|---------|
| email | Yes (username) | Yes | Auth + queries |
| phone | **Yes (phone_number)** | Yes | Future SMS login + booking contact |
| name | **Yes (name)** | Yes | UI display + booking records |

**Implementation Changes Required**:
1. Update Cognito User Pool to allow `phone_number` and `name` attributes (Terraform)
2. Update backend to save profile fields to Cognito during registration/update
3. Update frontend to read profile from Cognito session attributes (not DynamoDB lookup)
4. Keep DynamoDB `customers` table for booking queries (unchanged)

**Cognito Attribute Configuration** (Terraform):
```hcl
schema {
  name                = "email"
  attribute_data_type = "String"
  mutable            = true
  required           = true
}

schema {
  name                = "phone_number"
  attribute_data_type = "String"
  mutable            = true
  required           = false  # Optional for now, required for SMS login
}

schema {
  name                = "name"
  attribute_data_type = "String"
  mutable            = true
  required           = false  # Optional initially
}
```

### 8. Next.js Routing Best Practices

**Decision**: Implement route groups, convention files, and theme-aware loading states

**Rationale**:
- Next.js App Router provides `loading.tsx` and `error.tsx` convention files for automatic UI during route transitions
- Route groups `(auth)` organize related routes without affecting URL structure
- Current auth pages use hardcoded Tailwind colors (`bg-gray-50`, `text-gray-500`) violating FR-012 pattern
- Shared layout enables consistent auth page styling across login and callback

**Current Issues Found**:
| File | Issue | Fix |
|------|-------|-----|
| `auth/login/page.tsx:24,169,188` | Hardcoded `bg-gray-50`, `bg-red-50` colors | Use theme-aware classes |
| `auth/callback/page.tsx:52,154` | Hardcoded `bg-gray-50` colors | Use theme-aware classes |
| `auth/*` structure | No route group organization | Move to `(auth)/` |
| Missing convention files | No `loading.tsx`, `error.tsx` | Create with shadcn components |

**Implementation Pattern**:

**Route Group Layout** (`(auth)/layout.tsx`):
```tsx
export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-background px-4">
      <div className="max-w-md w-full space-y-8">
        {children}
      </div>
    </div>
  )
}
```

**Loading Convention** (`(auth)/loading.tsx`):
```tsx
import { Skeleton } from '@/components/ui/skeleton'

export default function AuthLoading() {
  return (
    <div className="space-y-4">
      <Skeleton className="h-8 w-48 mx-auto" />
      <Skeleton className="h-4 w-64 mx-auto" />
      <Skeleton className="h-12 w-full" />
    </div>
  )
}
```

**Error Convention** (`(auth)/error.tsx`):
```tsx
'use client'

import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { AlertCircle } from 'lucide-react'

export default function AuthError({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  return (
    <Alert variant="destructive">
      <AlertCircle className="h-4 w-4" />
      <AlertTitle>Authentication Error</AlertTitle>
      <AlertDescription>{error.message}</AlertDescription>
      <Button onClick={reset} className="mt-4">Try again</Button>
    </Alert>
  )
}
```

**Alternatives Considered**:
- Keep inline Suspense only: Rejected - misses route-level loading/error UI
- Use generic loading component: Rejected - shadcn Skeleton provides better UX
- Skip route group: Rejected - loses opportunity for shared layout and organization

## Summary

All research areas resolved. No NEEDS CLARIFICATION items remain.

| Research Item | Decision | Impact |
|---------------|----------|--------|
| Alert component | Use shadcn Alert variant="destructive" | AuthErrorBoundary rewrite |
| Badge component | Use shadcn Badge with status variant mapping | BookingSummaryCard update |
| ~~Dialog component~~ | ~~Use shadcn Dialog for PhotoGallery.tsx~~ **DELETE** PhotoGallery.tsx (dead code) | File deletion only |
| AuthStep types | Keep BOTH (verified different purposes), rename login page type to LoginStep | Minor rename only |
| Terminology | Full guest→customer rename | ~40 files affected |
| Dead code | **KEEP** `yet-another-react-lightbox` (used by `/gallery/`); **DELETE** `PhotoGallery.tsx` (unused) | No package.json changes; delete 1 file |
| Profile storage | Store ALL fields in Cognito + DynamoDB | Backend + Terraform changes |
| Next.js routing | Route groups, loading.tsx, error.tsx convention files | Auth routes reorganization |

**Critical Process Note**: For ANY duplicate removal, follow verification-first approach:
1. Analyze BOTH implementations
2. Document their purposes and test coverage
3. Determine if BOTH are needed (different purposes) or one is truly duplicate
4. Only remove after verification

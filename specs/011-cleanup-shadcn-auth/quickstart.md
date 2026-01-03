# Quickstart: Frontend Cleanup and Consistency

**Feature**: 011-cleanup-shadcn-auth
**Date**: 2026-01-03

## Prerequisites

- Node.js 18+ and Yarn 4.x
- Python 3.13+ and UV
- Terraform 1.5+
- AWS CLI configured with appropriate credentials
- All dependencies installed (`task install`)

## Quick Verification Commands

### Check Current State

```bash
# Verify no type conflicts (should find 2 files - this is the problem)
grep -r "type AuthStep" frontend/src/

# Check shadcn components installed
ls frontend/src/components/ui/

# Verify yet-another-react-lightbox is ONLY used in /gallery/page.tsx (KEEP it there)
# PhotoGallery.tsx uses a CUSTOM lightbox (to be migrated to shadcn Dialog)
grep -r "yet-another-react-lightbox" frontend/src/

# Check guest terminology usage (these should all be renamed)
grep -r "guest_id" backend/shared/src/
grep -r "GuestDetailsForm" frontend/src/
```

### Run Test Suite (Before Changes)

```bash
# Ensure everything works before starting
task test

# Or individually:
task frontend:test
task backend:test
task frontend:test:e2e
```

## Implementation Steps

### Step 1: Install Missing shadcn Components

```bash
cd frontend

# Install Alert component
npx shadcn@latest add alert

# Install Badge component
npx shadcn@latest add badge

# Verify installation
ls src/components/ui/
# Should now include: alert.tsx, badge.tsx
```

### Step 2: Migrate AuthErrorBoundary

```bash
# Edit the component
code frontend/src/components/booking/AuthErrorBoundary.tsx

# After editing, run tests
task frontend:test
```

### Step 3: Migrate BookingSummaryCard

```bash
code frontend/src/components/agent/BookingSummaryCard.tsx
task frontend:test
```

### Step 4: Delete PhotoGallery Dead Code

```bash
# PhotoGallery.tsx is dead code (zero imports anywhere in codebase)
# Verify it's still unused before deleting:
grep -r "PhotoGallery" frontend/src/ | grep -v "PhotoGallery.tsx"
# Should return empty (no imports exist)

# Delete the dead code file
rm frontend/src/components/agent/PhotoGallery.tsx

# Verify tests still pass
task frontend:test
```

### Step 5: Resolve AuthStep Type Conflict

```bash
# Rename type in login page
code frontend/src/app/auth/login/page.tsx
# Change: type AuthStep → type LoginStep

# Verify no more conflicts
grep -r "type AuthStep" frontend/src/
# Should now find only 1 file (useAuthenticatedUser.ts)
```

### Step 6: Reorganize Auth Routes (Next.js Best Practices)

```bash
cd frontend/src/app

# Create route group directory
mkdir -p "(auth)/login" "(auth)/callback"

# Move existing auth pages
mv auth/login/page.tsx "(auth)/login/page.tsx"
mv auth/callback/page.tsx "(auth)/callback/page.tsx"

# Remove old auth directory (should be empty now)
rmdir auth/login auth/callback auth

# Create shared layout for auth pages
touch "(auth)/layout.tsx"

# Create loading and error convention files
touch "(auth)/loading.tsx"
touch "(auth)/error.tsx"
```

Edit the new files:
```bash
# Shared auth layout
code "frontend/src/app/(auth)/layout.tsx"

# Route-level loading UI using shadcn Skeleton
code "frontend/src/app/(auth)/loading.tsx"

# Route-level error boundary using shadcn Alert
code "frontend/src/app/(auth)/error.tsx"
```

Update inline Suspense fallbacks in moved pages:
```bash
# Replace hardcoded colors (bg-gray-50, text-gray-500) with theme-aware classes
code "frontend/src/app/(auth)/login/page.tsx"
code "frontend/src/app/(auth)/callback/page.tsx"
```

Verify routes still work:
```bash
task frontend:dev
# Navigate to http://localhost:3000/login - should still work (route group doesn't affect URL)
```

### Step 7: Infrastructure - DynamoDB Table + Cognito Attributes

```bash
# Update DynamoDB Terraform
code infrastructure/modules/dynamodb/main.tf
# Rename: module "guests" → module "customers"
# Update: hash_key = "customer_id"

# Update Cognito User Pool to store profile fields
code infrastructure/modules/cognito/main.tf
# Add schema attributes:
#   - phone_number (standard attribute)
#   - name (standard attribute)

# Plan changes
task tf:plan:dev
# Review the plan - should show:
#   - guests table destroy, customers table create
#   - Cognito schema updates

# Apply changes (data loss is acceptable)
task tf:apply:dev
```

### Step 8: Backend - Rename Models, Routes + Cognito Storage

```bash
# Rename model file
mv backend/shared/src/shared/models/guest.py backend/shared/src/shared/models/customer.py

# Rename tools file
mv backend/shared/src/shared/tools/guest.py backend/shared/src/shared/tools/customer.py

# Update all imports and class names
# Update routes/customers.py with merged functionality
# Delete routes/guests.py

# IMPORTANT: Update customer service to save profile to Cognito
# Edit backend/shared/src/shared/services/cognito.py
# Add adminUpdateUserAttributes call to save phone_number and name

# Run backend tests
task backend:test
```

### Step 9: Regenerate API Client

```bash
# Start backend to get OpenAPI spec
task backend:dev &

# Wait for server to start, then generate
sleep 5
cd frontend
task frontend:generate:api

# Kill backend dev server
kill %1
```

### Step 10: Frontend - Rename Components

```bash
# Rename component file
mv frontend/src/components/booking/GuestDetailsForm.tsx \
   frontend/src/components/booking/CustomerDetailsForm.tsx

# Update all imports throughout codebase
# Update component name in the file

# Run all tests
task frontend:test
```

### Step 11: Verify Dependencies (No Removal Needed)

```bash
cd frontend

# NOTE: Do NOT remove yet-another-react-lightbox - it IS used by /gallery/page.tsx
# The PhotoGallery.tsx component uses a CUSTOM lightbox (migrated to shadcn Dialog)
# but /gallery/page.tsx uses yet-another-react-lightbox with Thumbnails+Zoom plugins

# Verify no other unused dependencies
npx depcheck
# Expected: yet-another-react-lightbox should NOT appear as unused
```

### Step 12: Full Test Suite

```bash
# Run everything
task test

# Run E2E tests to verify auth flow
task frontend:test:e2e

# Build to check for any issues
task frontend:build
```

## Verification Checklist

After completing all steps, verify:

- [ ] `ls frontend/src/app/\(auth\)/` shows `layout.tsx`, `loading.tsx`, `error.tsx`, `login/`, `callback/`
- [ ] `grep -r "bg-gray-50" frontend/src/app/` returns 0 results in loading/fallback components
- [ ] `grep -r "type AuthStep" frontend/src/` returns only 1 file
- [ ] `grep -r "bg-red-50\|text-red-800" frontend/src/components/` returns 0 results
- [ ] `ls frontend/src/components/ui/` includes `alert.tsx` and `badge.tsx`
- [ ] `grep -r "yet-another-react-lightbox" frontend/` returns ONLY `/gallery/page.tsx` (this is correct - KEEP this library)
- [ ] `grep -r "guest_id" backend/shared/src/` returns 0 results
- [ ] `grep -r "GuestDetailsForm" frontend/src/` returns 0 results
- [ ] `task test` passes all tests
- [ ] `task frontend:build` succeeds with no bundle size increase

## Troubleshooting

### shadcn installation fails

```bash
# Check components.json exists
cat frontend/components.json

# If missing, initialize shadcn
npx shadcn@latest init
```

### Type errors after rename

```bash
# Regenerate API client
cd frontend
yarn generate:api

# Clear TypeScript cache
rm -rf frontend/.next frontend/node_modules/.cache
yarn typecheck
```

### DynamoDB table issues

```bash
# Check table exists
aws dynamodb describe-table --table-name booking-dev-customers

# If not, rerun Terraform
task tf:apply:dev
```

### Tests failing after migration

```bash
# Check for stale imports
grep -r "from.*guest" frontend/src/
grep -r "Guest" frontend/src/types/

# Update any remaining references
```

## Rollback

If something goes wrong:

```bash
# Revert git changes
git checkout -- .

# Or specific files
git checkout -- frontend/src/components/booking/AuthErrorBoundary.tsx

# For infrastructure, revert and apply
git checkout -- infrastructure/
task tf:apply:dev
```

# API Contract Changes: Guest → Customer Rename

**Feature**: 011-cleanup-shadcn-auth
**Date**: 2026-01-03

## Overview

This document summarizes API endpoint changes due to the guest→customer terminology rename.

## Endpoint Changes

### Existing Customer Routes (Keep)

These endpoints already exist in `routes/customers.py` and remain unchanged:

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/customers/me` | Get authenticated customer profile |
| POST | `/customers/me` | Create customer profile for authenticated user |
| PUT | `/customers/me` | Update authenticated customer profile |

### Routes to Migrate (from `routes/guests.py`)

These endpoints will be consolidated into `routes/customers.py`:

| Current | New | Method | Description |
|---------|-----|--------|-------------|
| `/guests/verify` | `/customers/verify` | POST | Initiate email verification |
| `/guests/verify/confirm` | `/customers/verify/confirm` | POST | Confirm OTP code |
| `/guests/by-email/{email}` | `/customers/by-email/{email}` | GET | Get customer by email |
| `/guests/{guest_id}` | `/customers/{customer_id}` | PATCH | Update customer by ID |

### Request/Response Schema Changes

#### Verification Request (unchanged structure)
```json
{
  "email": "customer@example.com"
}
```

#### Verification Response (unchanged structure)
```json
{
  "message": "Verification code sent",
  "code_delivery_destination": "c***@example.com"
}
```

#### Customer Response (field rename)
**Before**:
```json
{
  "guest_id": "uuid-here",
  "email": "customer@example.com",
  "name": "John Doe",
  "phone": "+34612345678",
  "cognito_sub": "cognito-uuid"
}
```

**After**:
```json
{
  "customer_id": "uuid-here",
  "email": "customer@example.com",
  "name": "John Doe",
  "phone": "+34612345678",
  "cognito_sub": "cognito-uuid"
}
```

## OpenAPI Specification Updates

After backend changes, regenerate the OpenAPI spec:

```bash
# From backend directory
task backend:dev &
curl http://localhost:3001/openapi.json > ../frontend/openapi.json
```

Then regenerate the TypeScript client:

```bash
# From frontend directory
task frontend:generate:api
# or directly:
npx openapi-ts
```

## Migration Checklist

- [ ] Update `routes/guests.py` endpoints to use `/customers/` prefix
- [ ] Merge functionality into `routes/customers.py`
- [ ] Delete `routes/guests.py` after merge
- [ ] Update all response models: `guest_id` → `customer_id`
- [ ] Update OpenAPI tags: `guests` → `customers`
- [ ] Regenerate OpenAPI specification
- [ ] Regenerate frontend TypeScript client
- [ ] Update frontend API calls to use new endpoints
- [ ] Run integration tests to verify

## Breaking Changes

This is a **breaking change** for the API contract:

1. **Endpoint paths change**: `/guests/*` → `/customers/*`
2. **Field name changes**: `guest_id` → `customer_id`

Since this is a greenfield project with no external consumers, breaking changes are acceptable.

## Rollback Plan

If issues arise:
1. Revert backend route changes
2. Revert infrastructure changes (`terraform apply` with original config)
3. Regenerate frontend client with old schema

Data loss during rollback is acceptable per project phase.

# Data Model: Frontend Cleanup and Consistency

**Feature**: 011-cleanup-shadcn-auth
**Date**: 2026-01-03

## Entity Changes

This feature primarily renames the `Guest` entity to `Customer`. The entity structure remains unchanged.

### Cognito User Attributes (NEW)

Customer profile data is now stored in Cognito user attributes for faster UI session rendering and future SMS login support.

| Attribute | Type | Description | Cognito Attribute Name |
|-----------|------|-------------|------------------------|
| `email` | String | Email address (username) | `email` (standard) |
| `name` | String | Customer's full name | `name` (standard) |
| `phone` | String | Phone number | `phone_number` (standard) |

**Why Cognito storage?**
1. **Faster UI rendering**: Profile fields available in JWT/session without DynamoDB lookup
2. **Future SMS login**: `phone_number` attribute enables Cognito SMS_OTP auth flow
3. **Standard attributes**: Using Cognito standard attributes (not custom) for best compatibility

**Note**: Data is stored in BOTH Cognito (for session/UI) and DynamoDB (for booking queries).

### Customer Entity (renamed from Guest)

**Table**: `booking-{env}-customers` (renamed from `booking-{env}-guests`)

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| `customer_id` | String (PK) | UUID identifier | Required, UUID format |
| `email` | String | Email address | Required, valid email format |
| `name` | String | Customer's full name | Required, non-empty |
| `phone` | String | Phone number | Required, E.164 format preferred |
| `cognito_sub` | String | Cognito user identifier | Required, set on verification |
| `created_at` | String | ISO 8601 timestamp | Auto-generated |
| `updated_at` | String | ISO 8601 timestamp | Auto-updated |

**Global Secondary Indexes**:
- `email-index`: PK = `email` (for lookups by email)
- `cognito-sub-index`: PK = `cognito_sub` (for session restoration)

### Pydantic Models (Backend)

**Before** (`backend/shared/src/shared/models/guest.py`):
```python
class Guest(BaseModel):
    guest_id: str
    email: EmailStr
    name: str
    phone: str
    cognito_sub: str | None = None
    created_at: str | None = None
    updated_at: str | None = None

class GuestCreate(BaseModel):
    email: EmailStr
    name: str
    phone: str

class GuestUpdate(BaseModel):
    name: str | None = None
    phone: str | None = None
```

**After** (`backend/shared/src/shared/models/customer.py`):
```python
class Customer(BaseModel):
    customer_id: str
    email: EmailStr
    name: str
    phone: str
    cognito_sub: str | None = None
    created_at: str | None = None
    updated_at: str | None = None

class CustomerCreate(BaseModel):
    email: EmailStr
    name: str
    phone: str

class CustomerUpdate(BaseModel):
    name: str | None = None
    phone: str | None = None
```

### TypeScript Types (Frontend)

**Before** (`frontend/src/lib/api-client/types.gen.ts` - auto-generated):
```typescript
export type Guest = {
    guest_id: string;
    email: string;
    name: string;
    phone: string;
    cognito_sub?: string | null;
    created_at?: string | null;
    updated_at?: string | null;
};

export type GuestCreate = {
    email: string;
    name: string;
    phone: string;
};
```

**After** (auto-regenerated from OpenAPI):
```typescript
export type Customer = {
    customer_id: string;
    email: string;
    name: string;
    phone: string;
    cognito_sub?: string | null;
    created_at?: string | null;
    updated_at?: string | null;
};

export type CustomerCreate = {
    email: string;
    name: string;
    phone: string;
};
```

## Type Definitions (Non-Entity)

### AuthStep Types

**Canonical Definition** (`frontend/src/hooks/useAuthenticatedUser.ts`):
```typescript
export type AuthStep =
  | 'anonymous'      // Not authenticated, show input fields
  | 'sending_otp'    // OTP being sent
  | 'awaiting_otp'   // Waiting for user to enter OTP
  | 'verifying'      // Verifying OTP
  | 'authenticated'  // Authenticated, show read-only info
```

**Login Page Local Type** (`frontend/src/app/auth/login/page.tsx`):
```typescript
// Renamed from AuthStep to avoid conflict
type LoginStep = 'email' | 'otp' | 'success' | 'error'
```

## DynamoDB Table Changes

### Infrastructure Update

**Before** (`infrastructure/modules/dynamodb/main.tf`):
```hcl
module "guests" {
  source  = "terraform-aws-modules/dynamodb-table/aws"
  name    = "${module.label.id}-guests"

  hash_key = "guest_id"
  # ... GSIs for email and cognito_sub
}
```

**After**:
```hcl
module "customers" {
  source  = "terraform-aws-modules/dynamodb-table/aws"
  name    = "${module.label.id}-customers"

  hash_key = "customer_id"
  # ... GSIs for email and cognito_sub
}
```

### Migration Strategy

Since this is a greenfield project in development phase:
1. No data migration required
2. `terraform apply` will:
   - Destroy `guests` table
   - Create `customers` table
3. Any existing dev data will be lost (acceptable per spec clarification)

## Relationships

```
Customer 1 ───< N Reservation
    │
    │ (identified by)
    │
    └── Cognito User Pool (email-based auth + profile attributes)
```

- **Customer → Reservation**: One customer can have many reservations
- **Customer → Cognito**: One-to-one mapping via `cognito_sub`
- **Cognito stores**: ALL profile fields (email as username, phone_number, name) for UI session attributes and future SMS login
- **DynamoDB stores**: Full profile (email, name, phone) for booking queries and relationships

## Validation Rules

| Field | Rule | Error Message |
|-------|------|---------------|
| `customer_id` | Valid UUID v4 | "Invalid customer ID format" |
| `email` | RFC 5322 compliant | "Invalid email format" |
| `name` | Non-empty, max 100 chars | "Name is required" / "Name too long" |
| `phone` | Non-empty, E.164 preferred | "Phone number is required" |

## State Transitions

### Customer Lifecycle

```
[New User]
    │
    ├─ Submit form → [Unverified Customer Record]
    │                      │
    │                      ├─ Send OTP
    │                      │
    │                      └─ Verify OTP → [Verified Customer]
    │                                           │
    │                                           └─ (cognito_sub set)
    │
    └─ Returning User → [Existing Customer]
                             │
                             └─ Session restore via cognito_sub
```

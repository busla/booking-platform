# Data Model: Agent-First Vacation Rental Booking Platform

**Feature**: 001-agent-booking-platform
**Date**: 2025-12-27
**Storage**: AWS DynamoDB (Pay-Per-Request)

## Overview

This document defines the data model for the Booking vacation rental platform. All entities are stored in DynamoDB tables optimized for the access patterns required by the agent tools and API endpoints.

## Entity Relationship Diagram

```
┌─────────────┐       ┌─────────────────┐       ┌─────────────┐
│   Guest     │───1:N─│   Reservation   │───1:N─│   Payment   │
└─────────────┘       └─────────────────┘       └─────────────┘
                              │
                              │ references
                              ▼
┌─────────────┐       ┌─────────────────┐
│   Pricing   │       │  Availability   │
└─────────────┘       └─────────────────┘

┌─────────────┐       ┌─────────────────┐       ┌─────────────────┐
│  Apartment  │       │    AreaInfo     │       │  Conversation   │
└─────────────┘       └─────────────────┘       └─────────────────┘
     (static)              (static)                  (AgentCore
                                                      Memory)
```

## DynamoDB Tables

### 1. Reservations Table

**Table Name**: `booking-{env}-reservations`

| Attribute | Type | Key | Description |
|-----------|------|-----|-------------|
| `reservation_id` | String | PK | Unique reservation ID (e.g., `RES-2025-001234`) |
| `guest_id` | String | GSI-PK | Reference to Guest |
| `check_in` | String | GSI-SK | Check-in date (YYYY-MM-DD) |
| `check_out` | String | | Check-out date (YYYY-MM-DD) |
| `num_adults` | Number | | Number of adult guests |
| `num_children` | Number | | Number of child guests |
| `status` | String | | `pending`, `confirmed`, `cancelled`, `completed` |
| `payment_status` | String | | `pending`, `paid`, `refunded`, `partial_refund` |
| `total_amount` | Number | | Total price in EUR (cents) |
| `cleaning_fee` | Number | | Cleaning fee in EUR (cents) |
| `nightly_rate` | Number | | Rate per night in EUR (cents) |
| `nights` | Number | | Number of nights |
| `special_requests` | String | | Guest special requests |
| `created_at` | String | | ISO 8601 timestamp |
| `updated_at` | String | | ISO 8601 timestamp |
| `cancelled_at` | String | | ISO 8601 timestamp (if cancelled) |
| `cancellation_reason` | String | | Reason for cancellation |
| `refund_amount` | Number | | Refund amount in EUR (cents) |

**Indexes**:
- **Primary Key**: `reservation_id` (PK)
- **GSI: guest-checkin-index**: `guest_id` (PK), `check_in` (SK) - Find reservations by guest
- **GSI: status-index**: `status` (PK), `check_in` (SK) - Find reservations by status

**Access Patterns**:
| Pattern | Index | Query |
|---------|-------|-------|
| Get reservation by ID | Primary | `PK = reservation_id` |
| Get guest's reservations | guest-checkin-index | `guest_id = X` |
| Get guest's upcoming reservations | guest-checkin-index | `guest_id = X AND check_in >= today` |
| Get reservations by status | status-index | `status = X` |
| Get pending reservations | status-index | `status = 'pending'` |

**Pydantic Model**:
```python
from pydantic import BaseModel, ConfigDict
from enum import Enum
from datetime import date, datetime
from typing import Optional

class ReservationStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"

class PaymentStatus(str, Enum):
    PENDING = "pending"
    PAID = "paid"
    REFUNDED = "refunded"
    PARTIAL_REFUND = "partial_refund"

class Reservation(BaseModel):
    model_config = ConfigDict(strict=True)

    reservation_id: str
    guest_id: str
    check_in: date
    check_out: date
    num_adults: int
    num_children: int = 0
    status: ReservationStatus
    payment_status: PaymentStatus
    total_amount: int  # EUR cents
    cleaning_fee: int
    nightly_rate: int
    nights: int
    special_requests: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    cancelled_at: Optional[datetime] = None
    cancellation_reason: Optional[str] = None
    refund_amount: Optional[int] = None
```

---

### 2. Guests Table

**Table Name**: `booking-{env}-guests`

| Attribute | Type | Key | Description |
|-----------|------|-----|-------------|
| `guest_id` | String | PK | Unique guest ID (UUID) |
| `email` | String | GSI-PK | Guest email (verified) |
| `name` | String | | Full name |
| `phone` | String | | Phone number |
| `preferred_language` | String | | `en`, `es` |
| `email_verified` | Boolean | | Whether email is verified |
| `first_verified_at` | String | | First verification timestamp |
| `total_bookings` | Number | | Count of completed bookings |
| `notes` | String | | Internal notes |
| `created_at` | String | | ISO 8601 timestamp |
| `updated_at` | String | | ISO 8601 timestamp |

**Indexes**:
- **Primary Key**: `guest_id` (PK)
- **GSI: email-index**: `email` (PK) - Lookup guest by email

**Access Patterns**:
| Pattern | Index | Query |
|---------|-------|-------|
| Get guest by ID | Primary | `PK = guest_id` |
| Get guest by email | email-index | `email = X` |
| Check if email exists | email-index | `email = X` |

**Pydantic Model**:
```python
class Guest(BaseModel):
    model_config = ConfigDict(strict=True)

    guest_id: str
    email: str
    name: Optional[str] = None
    phone: Optional[str] = None
    preferred_language: str = "en"
    email_verified: bool = False
    first_verified_at: Optional[datetime] = None
    total_bookings: int = 0
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
```

---

### 3. Availability Table

**Table Name**: `booking-{env}-availability`

| Attribute | Type | Key | Description |
|-----------|------|-----|-------------|
| `date` | String | PK | Date (YYYY-MM-DD) |
| `status` | String | | `available`, `booked`, `blocked` |
| `reservation_id` | String | | Reference to Reservation (if booked) |
| `block_reason` | String | | Reason for manual block |
| `updated_at` | String | | ISO 8601 timestamp |

**Indexes**:
- **Primary Key**: `date` (PK)

**Access Patterns**:
| Pattern | Index | Query |
|---------|-------|-------|
| Get availability for date | Primary | `PK = date` |
| Get availability for range | Primary | BatchGetItem for date range |
| Check if dates available | Primary | BatchGetItem + filter `status = 'available'` |

**Pydantic Model**:
```python
class AvailabilityStatus(str, Enum):
    AVAILABLE = "available"
    BOOKED = "booked"
    BLOCKED = "blocked"

class Availability(BaseModel):
    model_config = ConfigDict(strict=True)

    date: date
    status: AvailabilityStatus
    reservation_id: Optional[str] = None
    block_reason: Optional[str] = None
    updated_at: datetime
```

**Implementation Notes**:
- Pre-populate 2 years of dates with `status = 'available'`
- Use DynamoDB conditional writes to prevent double-booking (FR-018, SC-006):
  ```python
  table.update_item(
      Key={'date': date_str},
      UpdateExpression='SET #status = :booked, reservation_id = :res_id',
      ConditionExpression='#status = :available',
      ExpressionAttributeNames={'#status': 'status'},
      ExpressionAttributeValues={
          ':booked': 'booked',
          ':available': 'available',
          ':res_id': reservation_id
      }
  )
  ```

---

### 4. Pricing Table

**Table Name**: `booking-{env}-pricing`

| Attribute | Type | Key | Description |
|-----------|------|-----|-------------|
| `season_id` | String | PK | Unique season ID (e.g., `high-2025`, `low-2025`) |
| `season_name` | String | | Display name (e.g., "High Season 2025") |
| `start_date` | String | | Season start date (YYYY-MM-DD) |
| `end_date` | String | | Season end date (YYYY-MM-DD) |
| `nightly_rate` | Number | | Rate per night in EUR (cents) |
| `minimum_nights` | Number | | Minimum stay requirement |
| `cleaning_fee` | Number | | Cleaning fee in EUR (cents) |
| `is_active` | Boolean | | Whether this pricing is active |

**Indexes**:
- **Primary Key**: `season_id` (PK)

**Access Patterns**:
| Pattern | Index | Query |
|---------|-------|-------|
| Get season by ID | Primary | `PK = season_id` |
| Get all pricing | Primary | Scan with filter `is_active = true` |

**Pydantic Model**:
```python
class Pricing(BaseModel):
    model_config = ConfigDict(strict=True)

    season_id: str
    season_name: str
    start_date: date
    end_date: date
    nightly_rate: int  # EUR cents
    minimum_nights: int
    cleaning_fee: int  # EUR cents
    is_active: bool = True
```

**Sample Data**:
```json
[
  {
    "season_id": "high-summer-2025",
    "season_name": "High Season (July-August)",
    "start_date": "2025-07-01",
    "end_date": "2025-08-31",
    "nightly_rate": 18000,
    "minimum_nights": 7,
    "cleaning_fee": 7500,
    "is_active": true
  },
  {
    "season_id": "mid-spring-2025",
    "season_name": "Mid Season (Spring)",
    "start_date": "2025-04-01",
    "end_date": "2025-06-30",
    "nightly_rate": 14000,
    "minimum_nights": 5,
    "cleaning_fee": 7500,
    "is_active": true
  },
  {
    "season_id": "low-winter-2025",
    "season_name": "Low Season (Winter)",
    "start_date": "2025-01-01",
    "end_date": "2025-03-31",
    "nightly_rate": 10000,
    "minimum_nights": 3,
    "cleaning_fee": 7500,
    "is_active": true
  }
]
```

---

### 5. Payments Table

**Table Name**: `booking-{env}-payments`

| Attribute | Type | Key | Description |
|-----------|------|-----|-------------|
| `payment_id` | String | PK | Unique payment ID |
| `reservation_id` | String | GSI-PK | Reference to Reservation |
| `amount` | Number | | Amount in EUR (cents) |
| `currency` | String | | Currency code (EUR) |
| `status` | String | | `pending`, `completed`, `failed`, `refunded` |
| `payment_method` | String | | `card`, `paypal`, `bank_transfer` |
| `provider` | String | | Payment provider (e.g., `stripe`, `mock`) |
| `provider_transaction_id` | String | | External transaction reference |
| `created_at` | String | | ISO 8601 timestamp |
| `completed_at` | String | | ISO 8601 timestamp |
| `error_message` | String | | Error details (if failed) |

**Indexes**:
- **Primary Key**: `payment_id` (PK)
- **GSI: reservation-index**: `reservation_id` (PK) - Get payments for reservation

**Access Patterns**:
| Pattern | Index | Query |
|---------|-------|-------|
| Get payment by ID | Primary | `PK = payment_id` |
| Get payments for reservation | reservation-index | `reservation_id = X` |

**Pydantic Model**:
```python
class PaymentMethod(str, Enum):
    CARD = "card"
    PAYPAL = "paypal"
    BANK_TRANSFER = "bank_transfer"

class PaymentProvider(str, Enum):
    STRIPE = "stripe"
    MOCK = "mock"

class Payment(BaseModel):
    model_config = ConfigDict(strict=True)

    payment_id: str
    reservation_id: str
    amount: int  # EUR cents
    currency: str = "EUR"
    status: str
    payment_method: PaymentMethod
    provider: PaymentProvider
    provider_transaction_id: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
```

---

### 6. Verification Codes Table (Cognito Support)

**Table Name**: `booking-{env}-verification-codes`

| Attribute | Type | Key | Description |
|-----------|------|-----|-------------|
| `email` | String | PK | Guest email |
| `code` | String | | 6-digit verification code |
| `expires_at` | Number | | Unix timestamp (TTL) |
| `attempts` | Number | | Failed attempt count |
| `created_at` | String | | ISO 8601 timestamp |

**Indexes**:
- **Primary Key**: `email` (PK)

**TTL**: `expires_at` - DynamoDB auto-deletes expired items

**Access Patterns**:
| Pattern | Index | Query |
|---------|-------|-------|
| Get code for email | Primary | `PK = email` |
| Validate code | Primary | `PK = email`, check `code` and `expires_at` |

---

## Static Content (S3/CDN or Database)

### Apartment Details

Stored as JSON in S3 or a single DynamoDB item:

```json
{
  "property_id": "booking-quesada",
  "name": "Quesada Apartment",
  "description": "Beautiful vacation apartment in Quesada, Alicante...",
  "address": {
    "street": "Calle Example 123",
    "city": "Ciudad Quesada",
    "region": "Alicante",
    "country": "Spain",
    "postal_code": "03170"
  },
  "coordinates": {
    "latitude": 38.0731,
    "longitude": -0.7835
  },
  "bedrooms": 2,
  "bathrooms": 1,
  "max_guests": 4,
  "amenities": [
    "WiFi",
    "Air Conditioning",
    "Parking",
    "Community Pool",
    "Fully Equipped Kitchen",
    "Washing Machine",
    "TV",
    "Terrace"
  ],
  "photos": [
    {
      "id": "living-room-1",
      "url": "https://cdn.booking.example/photos/living-room-1.jpg",
      "caption": "Spacious living room",
      "category": "living_room"
    },
    {
      "id": "bedroom-1",
      "url": "https://cdn.booking.example/photos/bedroom-1.jpg",
      "caption": "Master bedroom with double bed",
      "category": "bedroom"
    }
  ],
  "check_in_time": "15:00",
  "check_out_time": "10:00",
  "house_rules": [
    "No smoking",
    "No pets",
    "No parties or events"
  ]
}
```

### Area Information

Stored as JSON in S3 or DynamoDB:

```json
{
  "golf_courses": [
    {
      "name": "La Marquesa Golf",
      "distance_km": 3,
      "description": "18-hole course with stunning views"
    },
    {
      "name": "Vistabella Golf",
      "distance_km": 8,
      "description": "Championship course"
    }
  ],
  "beaches": [
    {
      "name": "Guardamar Beach",
      "distance_km": 15,
      "description": "Long sandy beach with dunes"
    },
    {
      "name": "La Mata Beach",
      "distance_km": 12,
      "description": "Blue flag beach"
    }
  ],
  "restaurants": [
    {
      "name": "La Taberna",
      "distance_km": 1,
      "cuisine": "Spanish tapas",
      "price_range": "€€"
    }
  ],
  "attractions": [
    {
      "name": "Torrevieja Salt Lakes",
      "distance_km": 10,
      "description": "Pink salt lakes, great for photos"
    }
  ],
  "family_activities": [
    {
      "name": "Aquopolis Torrevieja",
      "distance_km": 12,
      "description": "Water park"
    }
  ]
}
```

---

## Data Integrity Rules

### Reservation Workflow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   PENDING   │────▶│  CONFIRMED  │────▶│  COMPLETED  │     │  CANCELLED  │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
       │                   │                                       ▲
       │                   │                                       │
       └───────────────────┴───────────────────────────────────────┘
                         (cancellation)
```

### Double-Booking Prevention (SC-006)

1. **Atomic Availability Update**: Use DynamoDB conditional writes
2. **Transaction Pattern**:
   ```python
   # Use TransactWriteItems for multi-date bookings
   client.transact_write_items(
       TransactItems=[
           {
               'Update': {
                   'TableName': 'availability',
                   'Key': {'date': {'S': date}},
                   'UpdateExpression': 'SET #s = :booked, reservation_id = :rid',
                   'ConditionExpression': '#s = :available',
                   'ExpressionAttributeNames': {'#s': 'status'},
                   'ExpressionAttributeValues': {
                       ':booked': {'S': 'booked'},
                       ':available': {'S': 'available'},
                       ':rid': {'S': reservation_id}
                   }
               }
           }
           for date in date_range
       ]
   )
   ```

### Cancellation Policy

Based on spec.md assumptions:
- **14+ days before check-in**: Full refund
- **7-14 days before check-in**: 50% refund
- **< 7 days before check-in**: No refund

---

## Terraform Resources

```hcl
# DynamoDB Tables
resource "aws_dynamodb_table" "reservations" {
  name         = "booking-${var.environment}-reservations"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "reservation_id"

  attribute {
    name = "reservation_id"
    type = "S"
  }

  attribute {
    name = "guest_id"
    type = "S"
  }

  attribute {
    name = "check_in"
    type = "S"
  }

  attribute {
    name = "status"
    type = "S"
  }

  global_secondary_index {
    name            = "guest-checkin-index"
    hash_key        = "guest_id"
    range_key       = "check_in"
    projection_type = "ALL"
  }

  global_secondary_index {
    name            = "status-index"
    hash_key        = "status"
    range_key       = "check_in"
    projection_type = "ALL"
  }

  tags = var.tags
}

resource "aws_dynamodb_table" "guests" {
  name         = "booking-${var.environment}-guests"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "guest_id"

  attribute {
    name = "guest_id"
    type = "S"
  }

  attribute {
    name = "email"
    type = "S"
  }

  global_secondary_index {
    name            = "email-index"
    hash_key        = "email"
    projection_type = "ALL"
  }

  tags = var.tags
}

resource "aws_dynamodb_table" "availability" {
  name         = "booking-${var.environment}-availability"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "date"

  attribute {
    name = "date"
    type = "S"
  }

  tags = var.tags
}

resource "aws_dynamodb_table" "pricing" {
  name         = "booking-${var.environment}-pricing"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "season_id"

  attribute {
    name = "season_id"
    type = "S"
  }

  tags = var.tags
}

resource "aws_dynamodb_table" "payments" {
  name         = "booking-${var.environment}-payments"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "payment_id"

  attribute {
    name = "payment_id"
    type = "S"
  }

  attribute {
    name = "reservation_id"
    type = "S"
  }

  global_secondary_index {
    name            = "reservation-index"
    hash_key        = "reservation_id"
    projection_type = "ALL"
  }

  tags = var.tags
}

resource "aws_dynamodb_table" "verification_codes" {
  name         = "booking-${var.environment}-verification-codes"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "email"

  attribute {
    name = "email"
    type = "S"
  }

  ttl {
    attribute_name = "expires_at"
    enabled        = true
  }

  tags = var.tags
}
```

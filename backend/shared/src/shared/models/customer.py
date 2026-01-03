"""Customer model for customer records."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class Customer(BaseModel):
    """A registered customer in the system."""

    model_config = ConfigDict(strict=True)

    customer_id: str = Field(..., description="Unique customer ID (UUID)")
    email: EmailStr = Field(..., description="Customer email (verified)")
    cognito_sub: str | None = Field(
        default=None,
        description="Cognito User Pool subject identifier for OAuth2 binding",
    )
    name: str | None = Field(default=None, description="Full name")
    phone: str | None = Field(default=None, description="Phone number")
    preferred_language: str = Field(
        default="en", pattern="^(en|es)$", description="Preferred language"
    )
    email_verified: bool = Field(default=False, description="Email verification status")
    first_verified_at: datetime | None = Field(
        default=None, description="First verification timestamp"
    )
    total_bookings: int = Field(
        default=0, ge=0, description="Count of completed bookings"
    )
    notes: str | None = Field(default=None, description="Internal notes")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class CustomerCreate(BaseModel):
    """Data required to create a new customer."""

    model_config = ConfigDict(strict=True)

    email: EmailStr
    name: str | None = None
    phone: str | None = None
    preferred_language: str = Field(default="en", pattern="^(en|es)$")


class CustomerUpdate(BaseModel):
    """Fields that can be updated for a customer."""

    model_config = ConfigDict(strict=True)

    name: str | None = None
    phone: str | None = None
    preferred_language: str | None = Field(default=None, pattern="^(en|es)$")

"""Reservation model for booking records."""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from .enums import PaymentStatus, ReservationStatus


class Reservation(BaseModel):
    """A vacation rental reservation.

    Amounts are stored in EUR cents to avoid floating point issues.
    """

    model_config = ConfigDict(strict=True)

    reservation_id: str = Field(
        ..., description="Unique reservation ID (e.g., RES-2025-001234)"
    )
    guest_id: str = Field(..., description="Reference to Guest")
    check_in: date = Field(..., description="Check-in date")
    check_out: date = Field(..., description="Check-out date")
    num_adults: int = Field(..., ge=1, description="Number of adult guests")
    num_children: int = Field(default=0, ge=0, description="Number of child guests")
    status: ReservationStatus = Field(..., description="Reservation status")
    payment_status: PaymentStatus = Field(..., description="Payment status")
    total_amount: int = Field(..., ge=0, description="Total price in EUR cents")
    cleaning_fee: int = Field(..., ge=0, description="Cleaning fee in EUR cents")
    nightly_rate: int = Field(..., ge=0, description="Rate per night in EUR cents")
    nights: int = Field(..., ge=1, description="Number of nights")
    special_requests: str | None = Field(
        default=None, description="Guest special requests"
    )
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    cancelled_at: datetime | None = Field(
        default=None, description="Cancellation timestamp"
    )
    cancellation_reason: str | None = Field(
        default=None, description="Reason for cancellation"
    )
    refund_amount: int | None = Field(
        default=None, ge=0, description="Refund amount in EUR cents"
    )


class ReservationCreate(BaseModel):
    """Data required to create a new reservation."""

    model_config = ConfigDict(strict=True)

    guest_id: str
    check_in: date
    check_out: date
    num_adults: int = Field(..., ge=1)
    num_children: int = Field(default=0, ge=0)
    special_requests: str | None = None


class ReservationSummary(BaseModel):
    """Summary view of a reservation for listings."""

    model_config = ConfigDict(strict=True)

    reservation_id: str
    check_in: date
    check_out: date
    status: ReservationStatus
    total_amount: int

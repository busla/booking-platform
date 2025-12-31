"""Availability model for date-based booking status."""

import datetime as dt

from pydantic import BaseModel, ConfigDict, Field

from .enums import AvailabilityStatus


class Availability(BaseModel):
    """Availability status for a single date."""

    model_config = ConfigDict(strict=True)

    date: dt.date = Field(..., description="Date (YYYY-MM-DD)")
    status: AvailabilityStatus = Field(..., description="Availability status")
    reservation_id: str | None = Field(
        default=None, description="Reference to Reservation if booked"
    )
    block_reason: str | None = Field(
        default=None, description="Reason for manual block"
    )
    updated_at: dt.datetime = Field(..., description="Last update timestamp")


class AvailabilityRange(BaseModel):
    """Request to check availability for a date range."""

    model_config = ConfigDict(strict=True)

    start_date: dt.date = Field(..., description="Start of date range")
    end_date: dt.date = Field(..., description="End of date range")


class AvailabilityResponse(BaseModel):
    """Response for availability check."""

    model_config = ConfigDict(strict=True)

    start_date: dt.date
    end_date: dt.date
    is_available: bool
    unavailable_dates: list[dt.date] = Field(
        default_factory=list, description="List of unavailable dates in range"
    )
    total_nights: int
    nightly_rate: int = Field(..., description="Rate per night in EUR cents")
    cleaning_fee: int = Field(..., description="Cleaning fee in EUR cents")
    total_amount: int = Field(..., description="Total price in EUR cents")

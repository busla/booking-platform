"""Pricing model for seasonal rates."""

from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class Pricing(BaseModel):
    """Seasonal pricing configuration.

    Amounts are stored in EUR cents.
    """

    model_config = ConfigDict(strict=True)

    season_id: str = Field(
        ..., description="Unique season ID (e.g., high-summer-2025)"
    )
    season_name: str = Field(
        ..., description="Display name (e.g., High Season (July-August))"
    )
    start_date: date = Field(..., description="Season start date")
    end_date: date = Field(..., description="Season end date")
    nightly_rate: int = Field(..., ge=0, description="Rate per night in EUR cents")
    minimum_nights: int = Field(..., ge=1, description="Minimum stay requirement")
    cleaning_fee: int = Field(..., ge=0, description="Cleaning fee in EUR cents")
    is_active: bool = Field(default=True, description="Whether pricing is active")


class PricingCreate(BaseModel):
    """Data required to create pricing configuration."""

    model_config = ConfigDict(strict=True)

    season_id: str
    season_name: str
    start_date: date
    end_date: date
    nightly_rate: int = Field(..., ge=0)
    minimum_nights: int = Field(..., ge=1)
    cleaning_fee: int = Field(..., ge=0)
    is_active: bool = True


class PriceCalculation(BaseModel):
    """Result of price calculation for a stay."""

    model_config = ConfigDict(strict=True)

    check_in: date
    check_out: date
    nights: int
    nightly_rate: int = Field(..., description="Effective nightly rate in EUR cents")
    subtotal: int = Field(..., description="nights * nightly_rate in EUR cents")
    cleaning_fee: int = Field(..., description="Cleaning fee in EUR cents")
    total_amount: int = Field(..., description="Total price in EUR cents")
    minimum_nights: int = Field(..., description="Minimum nights for this period")
    season_name: str = Field(..., description="Applicable season name")

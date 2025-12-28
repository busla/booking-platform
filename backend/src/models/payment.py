"""Payment model for transaction records."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from .enums import PaymentMethod, PaymentProvider, TransactionStatus


class Payment(BaseModel):
    """A payment transaction for a reservation.

    Amounts are stored in EUR cents.
    """

    model_config = ConfigDict(strict=True)

    payment_id: str = Field(..., description="Unique payment ID")
    reservation_id: str = Field(..., description="Reference to Reservation")
    amount: int = Field(..., ge=0, description="Amount in EUR cents")
    currency: str = Field(default="EUR", description="Currency code")
    status: TransactionStatus = Field(..., description="Transaction status")
    payment_method: PaymentMethod = Field(..., description="Payment method used")
    provider: PaymentProvider = Field(..., description="Payment provider")
    provider_transaction_id: str | None = Field(
        default=None, description="External transaction reference"
    )
    created_at: datetime = Field(..., description="Creation timestamp")
    completed_at: datetime | None = Field(
        default=None, description="Completion timestamp"
    )
    error_message: str | None = Field(
        default=None, description="Error details if failed"
    )


class PaymentCreate(BaseModel):
    """Data required to initiate a payment."""

    model_config = ConfigDict(strict=True)

    reservation_id: str
    amount: int = Field(..., ge=0)
    payment_method: PaymentMethod


class PaymentResult(BaseModel):
    """Result of a payment operation."""

    model_config = ConfigDict(strict=True)

    payment_id: str
    status: TransactionStatus
    provider_transaction_id: str | None = None
    error_message: str | None = None

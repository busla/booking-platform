"""Verification code model for email authentication."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class VerificationCode(BaseModel):
    """Email verification code for passwordless authentication."""

    model_config = ConfigDict(strict=True)

    email: EmailStr = Field(..., description="Customer email")
    code: str = Field(..., min_length=6, max_length=6, description="6-digit code")
    expires_at: int = Field(..., description="Unix timestamp (TTL)")
    attempts: int = Field(default=0, ge=0, description="Failed attempt count")
    created_at: datetime = Field(..., description="Creation timestamp")


class VerificationRequest(BaseModel):
    """Request to send a verification code."""

    model_config = ConfigDict(strict=True)

    email: EmailStr


class VerificationAttempt(BaseModel):
    """Attempt to verify a code."""

    model_config = ConfigDict(strict=True)

    email: EmailStr
    code: str = Field(..., min_length=6, max_length=6)


class VerificationResult(BaseModel):
    """Result of verification attempt."""

    model_config = ConfigDict(strict=True)

    success: bool
    customer_id: str | None = None
    error: str | None = None
    is_new_customer: bool = False

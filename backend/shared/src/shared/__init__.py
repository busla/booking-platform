"""Shared models, services, and tools for the Booking platform.

This package contains:
- models: Pydantic models for all data entities
- services: Business logic and external service integrations
- tools: Strands agent tool functions
- utils: Helper functions and utilities
"""

__version__ = "0.1.0"

# Re-export commonly used items for convenience
from shared.models import (
    # Core enums
    AvailabilityStatus,
    PaymentStatus,
    ReservationStatus,
    # Key models
    Customer,
    Reservation,
    Property,
    Payment,
    # Error types
    BookingError,
    ErrorCode,
    ToolError,
)

__all__ = [
    "__version__",
    # Enums
    "AvailabilityStatus",
    "PaymentStatus",
    "ReservationStatus",
    # Models
    "Customer",
    "Reservation",
    "Property",
    "Payment",
    # Errors
    "BookingError",
    "ErrorCode",
    "ToolError",
]

"""Payment tools for processing reservation payments.

These tools handle payment processing for reservations.
Currently implements a mock payment provider that always succeeds.
In production, integrate with Stripe, PayPal, etc.
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from strands import tool

logger = logging.getLogger(__name__)

from src.models.enums import (
    PaymentMethod,
    PaymentProvider,
    PaymentStatus,
    ReservationStatus,
    TransactionStatus,
)
from src.models.errors import ErrorCode, ToolError
from src.services.dynamodb import get_dynamodb_service


def _get_db():
    """Get shared DynamoDB service instance (singleton for performance)."""
    return get_dynamodb_service()


def _generate_transaction_id() -> str:
    """Generate a unique transaction ID."""
    return f"TXN-{uuid.uuid4().hex[:12].upper()}"


@tool
def process_payment(
    reservation_id: str,
    payment_method: str = "card",
) -> dict[str, Any]:
    """Process payment for a reservation.

    Use this tool when a guest is ready to pay for their booking.
    The payment is processed and the reservation is confirmed upon success.

    NOTE: This is a mock implementation that always succeeds.
    In production, this would integrate with Stripe, PayPal, etc.

    Args:
        reservation_id: The reservation ID to pay for (e.g., 'RES-2025-ABCD1234')
        payment_method: Payment method - 'card', 'paypal', or 'bank_transfer' (default: 'card')

    Returns:
        Dictionary with payment result and updated reservation status
    """
    logger.info("process_payment called", extra={"reservation_id": reservation_id, "payment_method": payment_method})
    db = _get_db()

    # Validate payment method
    valid_methods = [m.value for m in PaymentMethod]
    if payment_method not in valid_methods:
        return {
            "status": "error",
            "message": f"Invalid payment method. Valid options: {', '.join(valid_methods)}",
        }

    # Get reservation
    reservation = db.get_item("reservations", {"reservation_id": reservation_id})

    if not reservation:
        error = ToolError.from_code(
            ErrorCode.RESERVATION_NOT_FOUND,
            details={"reservation_id": reservation_id},
        )
        return error.model_dump()

    # Check if already paid
    if reservation.get("payment_status") == PaymentStatus.PAID.value:
        error = ToolError.from_code(
            ErrorCode.PAYMENT_FAILED,
            details={"reason": "already_paid", "reservation_id": reservation_id},
        )
        return error.model_dump()

    # Check reservation status
    if reservation.get("status") == ReservationStatus.CANCELLED.value:
        error = ToolError.from_code(
            ErrorCode.UNAUTHORIZED,
            details={"reason": "reservation_cancelled", "reservation_id": reservation_id},
        )
        return error.model_dump()

    # Get amount to charge
    amount_cents = int(reservation["total_amount"])
    amount_eur = amount_cents / 100

    # Generate transaction ID
    transaction_id = _generate_transaction_id()
    now = datetime.now(timezone.utc)

    # MOCK: Simulate payment processing
    # In production, call Stripe/PayPal API here
    payment_success = True  # Mock always succeeds

    if not payment_success:
        # Handle payment failure (won't happen in mock)
        error = ToolError.from_code(
            ErrorCode.PAYMENT_FAILED,
            details={"reason": "processing_failed", "retry_allowed": "true"},
        )
        return error.model_dump()

    # Create payment record (payment_id is the PK, transaction_id is alias)
    payment_record = {
        "payment_id": transaction_id,  # Use transaction_id as payment_id
        "transaction_id": transaction_id,
        "reservation_id": reservation_id,
        "amount": amount_cents,
        "currency": "EUR",
        "payment_method": payment_method,
        "provider": PaymentProvider.MOCK.value,
        "status": TransactionStatus.COMPLETED.value,
        "created_at": now.isoformat(),
        "completed_at": now.isoformat(),
    }

    # Store payment record
    db.put_item("payments", payment_record)

    # Update reservation status
    db.update_item(
        "reservations",
        {"reservation_id": reservation_id},
        "SET #status = :confirmed, payment_status = :paid, updated_at = :now",
        {
            ":confirmed": ReservationStatus.CONFIRMED.value,
            ":paid": PaymentStatus.PAID.value,
            ":now": now.isoformat(),
        },
        expression_attribute_names={"#status": "status"},
    )

    return {
        "status": "success",
        "transaction_id": transaction_id,
        "reservation_id": reservation_id,
        "amount_eur": amount_eur,
        "amount_cents": amount_cents,
        "payment_method": payment_method,
        "reservation_status": ReservationStatus.CONFIRMED.value,
        "payment_status": PaymentStatus.PAID.value,
        "message": f"Payment of €{amount_eur:.2f} processed successfully! Your reservation {reservation_id} is now confirmed. You will receive a confirmation email shortly.",
    }


@tool
def get_payment_status(reservation_id: str) -> dict[str, Any]:
    """Check the payment status for a reservation.

    Use this tool when a guest asks about payment status
    or wants to verify if their payment went through.

    Args:
        reservation_id: The reservation ID to check (e.g., 'RES-2025-ABCD1234')

    Returns:
        Dictionary with payment status information
    """
    logger.info("get_payment_status called", extra={"reservation_id": reservation_id})
    db = _get_db()

    # Get reservation
    reservation = db.get_item("reservations", {"reservation_id": reservation_id})

    if not reservation:
        error = ToolError.from_code(
            ErrorCode.RESERVATION_NOT_FOUND,
            details={"reservation_id": reservation_id},
        )
        return error.model_dump()

    payment_status = reservation.get("payment_status", PaymentStatus.PENDING.value)
    reservation_status = reservation.get("status", ReservationStatus.PENDING.value)
    amount_eur = int(reservation["total_amount"]) / 100

    # Get payment record if exists
    # In production, query by reservation_id GSI
    payment_info = None
    try:
        # Simple scan for demo - use GSI in production
        from boto3.dynamodb.conditions import Key

        payments = db.query(
            "payments",
            Key("reservation_id").eq(reservation_id),
            index_name="reservation-index",
        )
        if payments:
            payment_info = payments[0]
    except Exception:
        pass

    result: dict[str, Any] = {
        "status": "success",
        "reservation_id": reservation_id,
        "payment_status": payment_status,
        "reservation_status": reservation_status,
        "amount_eur": amount_eur,
    }

    if payment_status == PaymentStatus.PAID.value:
        result["message"] = f"Payment of €{amount_eur:.2f} has been received. Your booking is confirmed!"
        if payment_info:
            result["transaction_id"] = payment_info.get("transaction_id")
            result["paid_at"] = payment_info.get("completed_at")
    elif payment_status == PaymentStatus.PENDING.value:
        result["message"] = f"Payment of €{amount_eur:.2f} is pending. Would you like to proceed with payment?"
        result["action_required"] = "payment"
    elif payment_status == PaymentStatus.REFUNDED.value:
        result["message"] = "Payment has been refunded."
        result["refund_amount_eur"] = int(reservation.get("refund_amount", 0)) / 100

    return result


@tool
def retry_payment(
    reservation_id: str,
    payment_method: str = "card",
) -> dict[str, Any]:
    """Retry a failed payment with a different payment method.

    Use this tool when a previous payment attempt failed
    and the guest wants to try again with the same or different method.

    Args:
        reservation_id: The reservation ID (e.g., 'RES-2025-ABCD1234')
        payment_method: Payment method to try - 'card', 'paypal', or 'bank_transfer'

    Returns:
        Dictionary with payment result
    """
    logger.info("retry_payment called", extra={"reservation_id": reservation_id, "payment_method": payment_method})
    # This essentially calls process_payment but with explicit retry semantics
    db = _get_db()

    # Check if reservation exists and is in retryable state
    reservation = db.get_item("reservations", {"reservation_id": reservation_id})

    if not reservation:
        error = ToolError.from_code(
            ErrorCode.RESERVATION_NOT_FOUND,
            details={"reservation_id": reservation_id},
        )
        return error.model_dump()

    if reservation.get("payment_status") == PaymentStatus.PAID.value:
        error = ToolError.from_code(
            ErrorCode.PAYMENT_FAILED,
            details={"reason": "already_paid", "reservation_id": reservation_id},
        )
        return error.model_dump()

    if reservation.get("status") == ReservationStatus.CANCELLED.value:
        error = ToolError.from_code(
            ErrorCode.UNAUTHORIZED,
            details={"reason": "reservation_cancelled", "reservation_id": reservation_id},
        )
        return error.model_dump()

    # Delegate to process_payment
    return process_payment(reservation_id, payment_method)

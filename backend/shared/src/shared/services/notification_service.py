"""Notification service for sending emails.

This service handles email notifications for reservations.
Currently implements a mock email sender that logs messages.
In production, integrate with Amazon SES.
"""

import datetime as dt
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class NotificationType(str, Enum):
    """Types of notification emails."""

    BOOKING_CONFIRMATION = "booking_confirmation"
    PAYMENT_RECEIVED = "payment_received"
    BOOKING_REMINDER = "booking_reminder"
    BOOKING_CANCELLED = "booking_cancelled"
    REFUND_PROCESSED = "refund_processed"
    VERIFICATION_CODE = "verification_code"


@dataclass
class EmailMessage:
    """Email message structure."""

    to: str
    subject: str
    body_text: str
    body_html: str | None = None
    notification_type: NotificationType | None = None
    metadata: dict[str, Any] | None = None


@dataclass
class NotificationResult:
    """Result of a notification operation."""

    success: bool
    message_id: str | None = None
    error: str | None = None


class NotificationService:
    """Service for sending email notifications.

    This is a mock implementation that logs emails.
    In production, replace with Amazon SES client.
    """

    def __init__(
        self,
        from_email: str = "noreply@quesada-apartment.com",
        from_name: str = "Quesada Apartment",
    ) -> None:
        """Initialize notification service.

        Args:
            from_email: Sender email address
            from_name: Sender display name
        """
        self.from_email = from_email
        self.from_name = from_name
        self._sent_messages: list[EmailMessage] = []  # For testing

    def send_email(self, message: EmailMessage) -> NotificationResult:
        """Send an email message.

        MOCK: Logs the email instead of actually sending.
        In production, use Amazon SES.

        Args:
            message: Email message to send

        Returns:
            NotificationResult with status
        """
        now = dt.datetime.now(dt.UTC)
        message_id = f"MOCK-{now.strftime('%Y%m%d%H%M%S')}-{id(message):x}"

        # MOCK: Log the email
        logger.info(
            "[MOCK EMAIL] To: %s | Subject: %s | Type: %s",
            message.to,
            message.subject,
            message.notification_type.value if message.notification_type else "generic",
        )
        logger.debug("[MOCK EMAIL] Body: %s", message.body_text[:200])

        # Store for testing
        self._sent_messages.append(message)

        return NotificationResult(success=True, message_id=message_id)

    def send_verification_code(
        self,
        email: str,
        code: str,
        expires_minutes: int = 10,
    ) -> NotificationResult:
        """Send a verification code email.

        Args:
            email: Recipient email address
            code: 6-digit verification code
            expires_minutes: Code expiration time

        Returns:
            NotificationResult
        """
        message = EmailMessage(
            to=email,
            subject="Your Quesada Apartment Verification Code",
            body_text=f"""Hello,

Your verification code is: {code}

This code will expire in {expires_minutes} minutes.

If you did not request this code, please ignore this email.

Best regards,
The Quesada Apartment Team
""",
            body_html=f"""
<html>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
    <h2 style="color: #2c5530;">Quesada Apartment</h2>
    <p>Hello,</p>
    <p>Your verification code is:</p>
    <div style="background: #f5f5f5; padding: 20px; text-align: center; font-size: 32px; letter-spacing: 5px; font-weight: bold; margin: 20px 0;">
        {code}
    </div>
    <p>This code will expire in {expires_minutes} minutes.</p>
    <p style="color: #666; font-size: 12px;">If you did not request this code, please ignore this email.</p>
    <p>Best regards,<br>The Quesada Apartment Team</p>
</body>
</html>
""",
            notification_type=NotificationType.VERIFICATION_CODE,
            metadata={"code": code, "expires_minutes": expires_minutes},
        )

        return self.send_email(message)

    def send_booking_confirmation(
        self,
        email: str,
        guest_name: str,
        reservation_id: str,
        check_in: str,
        check_out: str,
        total_amount: float,
        nights: int,
    ) -> NotificationResult:
        """Send a booking confirmation email.

        Args:
            email: Guest email address
            guest_name: Guest name
            reservation_id: Reservation ID
            check_in: Check-in date (ISO format)
            check_out: Check-out date (ISO format)
            total_amount: Total in EUR
            nights: Number of nights

        Returns:
            NotificationResult
        """
        message = EmailMessage(
            to=email,
            subject=f"Booking Confirmed - {reservation_id}",
            body_text=f"""Dear {guest_name or 'Guest'},

Your booking at Quesada Apartment has been confirmed!

Reservation Details:
- Confirmation Number: {reservation_id}
- Check-in: {check_in}
- Check-out: {check_out}
- Duration: {nights} night(s)
- Total: €{total_amount:.2f}

Address:
Urbanización La Marquesa
03140 Guardamar del Segura, Alicante
Spain

Check-in time: 3:00 PM
Check-out time: 10:00 AM

If you have any questions, please reply to this email.

We look forward to hosting you!

Best regards,
The Quesada Apartment Team
""",
            body_html=f"""
<html>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
    <h2 style="color: #2c5530;">Booking Confirmed!</h2>
    <p>Dear {guest_name or 'Guest'},</p>
    <p>Your booking at Quesada Apartment has been confirmed!</p>

    <div style="background: #f9f9f9; padding: 20px; border-radius: 8px; margin: 20px 0;">
        <h3 style="margin-top: 0;">Reservation Details</h3>
        <table style="width: 100%;">
            <tr><td style="padding: 5px 0;"><strong>Confirmation:</strong></td><td>{reservation_id}</td></tr>
            <tr><td style="padding: 5px 0;"><strong>Check-in:</strong></td><td>{check_in}</td></tr>
            <tr><td style="padding: 5px 0;"><strong>Check-out:</strong></td><td>{check_out}</td></tr>
            <tr><td style="padding: 5px 0;"><strong>Duration:</strong></td><td>{nights} night(s)</td></tr>
            <tr><td style="padding: 5px 0;"><strong>Total:</strong></td><td>€{total_amount:.2f}</td></tr>
        </table>
    </div>

    <div style="background: #e8f5e9; padding: 15px; border-radius: 8px; margin: 20px 0;">
        <strong>Address:</strong><br>
        Urbanización La Marquesa<br>
        03140 Guardamar del Segura, Alicante<br>
        Spain
    </div>

    <p><strong>Check-in time:</strong> 3:00 PM<br>
    <strong>Check-out time:</strong> 10:00 AM</p>

    <p>If you have any questions, please reply to this email.</p>
    <p>We look forward to hosting you!</p>

    <p>Best regards,<br>The Quesada Apartment Team</p>
</body>
</html>
""",
            notification_type=NotificationType.BOOKING_CONFIRMATION,
            metadata={
                "reservation_id": reservation_id,
                "check_in": check_in,
                "check_out": check_out,
                "total_amount": total_amount,
            },
        )

        return self.send_email(message)

    def send_payment_receipt(
        self,
        email: str,
        guest_name: str,
        reservation_id: str,
        transaction_id: str,
        amount: float,
        payment_method: str,
    ) -> NotificationResult:
        """Send a payment receipt email.

        Args:
            email: Guest email address
            guest_name: Guest name
            reservation_id: Reservation ID
            transaction_id: Payment transaction ID
            amount: Amount paid in EUR
            payment_method: Payment method used

        Returns:
            NotificationResult
        """
        message = EmailMessage(
            to=email,
            subject=f"Payment Received - {reservation_id}",
            body_text=f"""Dear {guest_name or 'Guest'},

We have received your payment for reservation {reservation_id}.

Payment Details:
- Transaction ID: {transaction_id}
- Amount: €{amount:.2f}
- Payment Method: {payment_method}

Thank you for your booking!

Best regards,
The Quesada Apartment Team
""",
            notification_type=NotificationType.PAYMENT_RECEIVED,
            metadata={
                "reservation_id": reservation_id,
                "transaction_id": transaction_id,
                "amount": amount,
            },
        )

        return self.send_email(message)

    def send_cancellation_notice(
        self,
        email: str,
        guest_name: str,
        reservation_id: str,
        check_in: str,
        refund_amount: float | None = None,
    ) -> NotificationResult:
        """Send a booking cancellation notice.

        Args:
            email: Guest email address
            guest_name: Guest name
            reservation_id: Reservation ID
            check_in: Original check-in date
            refund_amount: Refund amount if applicable

        Returns:
            NotificationResult
        """
        refund_text = ""
        if refund_amount is not None and refund_amount > 0:
            refund_text = f"\n\nA refund of €{refund_amount:.2f} will be processed within 5-10 business days."

        message = EmailMessage(
            to=email,
            subject=f"Booking Cancelled - {reservation_id}",
            body_text=f"""Dear {guest_name or 'Guest'},

Your booking {reservation_id} for check-in on {check_in} has been cancelled.{refund_text}

If you have any questions, please contact us.

Best regards,
The Quesada Apartment Team
""",
            notification_type=NotificationType.BOOKING_CANCELLED,
            metadata={
                "reservation_id": reservation_id,
                "check_in": check_in,
                "refund_amount": refund_amount,
            },
        )

        return self.send_email(message)

    def get_sent_messages(self) -> list[EmailMessage]:
        """Get list of sent messages (for testing).

        Returns:
            List of EmailMessage objects
        """
        return self._sent_messages.copy()

    def clear_sent_messages(self) -> None:
        """Clear sent messages list (for testing)."""
        self._sent_messages.clear()

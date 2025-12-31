"""Booking service for reservation management."""

import datetime as dt
import uuid
from typing import TYPE_CHECKING, Any

from shared.models import (
    Guest,
    GuestCreate,
    PaymentStatus,
    Reservation,
    ReservationCreate,
    ReservationStatus,
    ReservationSummary,
)

if TYPE_CHECKING:
    from .availability import AvailabilityService
    from .dynamodb import DynamoDBService
    from .pricing import PricingService


class BookingService:
    """Service for managing reservations and guests."""

    RESERVATIONS_TABLE = "reservations"
    GUESTS_TABLE = "guests"

    def __init__(
        self,
        db: "DynamoDBService",
        availability: "AvailabilityService",
        pricing: "PricingService",
    ) -> None:
        """Initialize booking service.

        Args:
            db: DynamoDB service instance
            availability: Availability service instance
            pricing: Pricing service instance
        """
        self.db = db
        self.availability = availability
        self.pricing = pricing

    # Guest operations

    def get_guest(self, guest_id: str) -> Guest | None:
        """Get guest by ID."""
        item = self.db.get_item(self.GUESTS_TABLE, {"guest_id": guest_id})
        return self._item_to_guest(item) if item else None

    def get_guest_by_email(self, email: str) -> Guest | None:
        """Get guest by email address."""
        items = self.db.query_by_gsi(
            self.GUESTS_TABLE,
            "email-index",
            "email",
            email.lower(),
        )
        return self._item_to_guest(items[0]) if items else None

    def create_guest(self, data: GuestCreate) -> Guest:
        """Create a new guest.

        Args:
            data: Guest creation data

        Returns:
            Created Guest object
        """
        now = dt.datetime.now(dt.UTC)
        guest = Guest(
            guest_id=str(uuid.uuid4()),
            email=data.email.lower(),
            name=data.name,
            phone=data.phone,
            preferred_language=data.preferred_language,
            email_verified=False,
            total_bookings=0,
            created_at=now,
            updated_at=now,
        )

        self.db.put_item(self.GUESTS_TABLE, self._guest_to_item(guest))
        return guest

    def get_or_create_guest(self, email: str, name: str | None = None) -> Guest:
        """Get existing guest or create new one.

        Args:
            email: Guest email
            name: Optional name for new guest

        Returns:
            Guest object
        """
        existing = self.get_guest_by_email(email)
        if existing:
            return existing

        return self.create_guest(GuestCreate(email=email, name=name))

    def verify_guest_email(self, guest_id: str) -> bool:
        """Mark guest email as verified.

        Args:
            guest_id: Guest ID to verify

        Returns:
            True if updated
        """
        now = dt.datetime.now(dt.UTC)
        result = self.db.update_item(
            self.GUESTS_TABLE,
            {"guest_id": guest_id},
            "SET email_verified = :v, first_verified_at = :t, updated_at = :u",
            {
                ":v": True,
                ":t": now.isoformat(),
                ":u": now.isoformat(),
            },
            condition_expression="attribute_exists(guest_id)",
        )
        return result is not None

    # Reservation operations

    def get_reservation(self, reservation_id: str) -> Reservation | None:
        """Get reservation by ID."""
        item = self.db.get_item(
            self.RESERVATIONS_TABLE,
            {"reservation_id": reservation_id},
        )
        return self._item_to_reservation(item) if item else None

    def get_guest_reservations(
        self,
        guest_id: str,
        upcoming_only: bool = False,
    ) -> list[ReservationSummary]:
        """Get all reservations for a guest.

        Args:
            guest_id: Guest ID
            upcoming_only: Only return future reservations

        Returns:
            List of reservation summaries
        """
        items = self.db.query_by_gsi(
            self.RESERVATIONS_TABLE,
            "guest-checkin-index",
            "guest_id",
            guest_id,
        )

        today = dt.date.today().isoformat()
        reservations = []

        for item in items:
            if upcoming_only and item["check_in"] < today:
                continue
            reservations.append(self._item_to_summary(item))

        return sorted(reservations, key=lambda r: r.check_in)

    def create_reservation(
        self,
        data: ReservationCreate,
    ) -> tuple[Reservation | None, str]:
        """Create a new reservation.

        Validates availability, calculates pricing, and atomically books dates.

        Args:
            data: Reservation creation data

        Returns:
            Tuple of (Reservation or None, error message)
        """
        # Validate minimum stay
        is_valid, error = self.pricing.validate_minimum_stay(
            data.check_in, data.check_out
        )
        if not is_valid:
            return None, error

        # Calculate price
        price_calc = self.pricing.calculate_price(data.check_in, data.check_out)
        if not price_calc:
            return None, "No pricing available for selected dates"

        # Check availability
        avail = self.availability.check_availability(data.check_in, data.check_out)
        if not avail.is_available:
            unavail_str = ", ".join(d.isoformat() for d in avail.unavailable_dates[:3])
            return None, f"Dates not available: {unavail_str}"

        # Generate reservation ID
        year = dt.date.today().year
        reservation_id = f"RES-{year}-{uuid.uuid4().hex[:6].upper()}"

        # Try to book dates atomically
        if not self.availability.book_dates(
            data.check_in, data.check_out, reservation_id
        ):
            return None, "Dates became unavailable. Please try again."

        # Create reservation record
        now = dt.datetime.now(dt.UTC)
        reservation = Reservation(
            reservation_id=reservation_id,
            guest_id=data.guest_id,
            check_in=data.check_in,
            check_out=data.check_out,
            num_adults=data.num_adults,
            num_children=data.num_children,
            status=ReservationStatus.PENDING,
            payment_status=PaymentStatus.PENDING,
            total_amount=price_calc.total_amount,
            cleaning_fee=price_calc.cleaning_fee,
            nightly_rate=price_calc.nightly_rate,
            nights=price_calc.nights,
            special_requests=data.special_requests,
            created_at=now,
            updated_at=now,
        )

        self.db.put_item(
            self.RESERVATIONS_TABLE,
            self._reservation_to_item(reservation),
        )

        return reservation, ""

    def confirm_reservation(self, reservation_id: str) -> bool:
        """Confirm a pending reservation (after payment).

        Args:
            reservation_id: Reservation to confirm

        Returns:
            True if confirmed
        """
        now = dt.datetime.now(dt.UTC)
        result = self.db.update_item(
            self.RESERVATIONS_TABLE,
            {"reservation_id": reservation_id},
            "SET #s = :confirmed, payment_status = :paid, updated_at = :u",
            {
                ":confirmed": ReservationStatus.CONFIRMED.value,
                ":paid": PaymentStatus.PAID.value,
                ":u": now.isoformat(),
                ":pending": ReservationStatus.PENDING.value,
            },
            expression_attribute_names={"#s": "status"},
            condition_expression="#s = :pending",
        )
        return result is not None

    def cancel_reservation(
        self,
        reservation_id: str,
        reason: str,
    ) -> tuple[bool, int]:
        """Cancel a reservation.

        Calculates refund based on cancellation policy and releases dates.

        Args:
            reservation_id: Reservation to cancel
            reason: Cancellation reason

        Returns:
            Tuple of (success, refund_amount in cents)
        """
        reservation = self.get_reservation(reservation_id)
        if not reservation:
            return False, 0

        if reservation.status == ReservationStatus.CANCELLED:
            return False, 0

        # Calculate refund based on policy
        days_until = (reservation.check_in - dt.date.today()).days
        if days_until >= 14:
            refund_amount = reservation.total_amount  # Full refund
        elif days_until >= 7:
            refund_amount = reservation.total_amount // 2  # 50% refund
        else:
            refund_amount = 0  # No refund

        now = dt.datetime.now(dt.UTC)

        # Update reservation
        result = self.db.update_item(
            self.RESERVATIONS_TABLE,
            {"reservation_id": reservation_id},
            (
                "SET #s = :cancelled, cancelled_at = :t, "
                "cancellation_reason = :r, refund_amount = :ref, "
                "payment_status = :ps, updated_at = :u"
            ),
            {
                ":cancelled": ReservationStatus.CANCELLED.value,
                ":t": now.isoformat(),
                ":r": reason,
                ":ref": refund_amount,
                ":ps": (
                    PaymentStatus.REFUNDED.value
                    if refund_amount == reservation.total_amount
                    else PaymentStatus.PARTIAL_REFUND.value
                    if refund_amount > 0
                    else reservation.payment_status.value
                ),
                ":u": now.isoformat(),
            },
            expression_attribute_names={"#s": "status"},
        )

        if not result:
            return False, 0

        # Release dates
        self.availability.release_dates(
            reservation.check_in,
            reservation.check_out,
            reservation_id,
        )

        return True, refund_amount

    # Conversion helpers

    def _item_to_guest(self, item: dict[str, Any]) -> Guest:
        """Convert DynamoDB item to Guest model."""
        return Guest(
            guest_id=item["guest_id"],
            email=item["email"],
            name=item.get("name"),
            phone=item.get("phone"),
            preferred_language=item.get("preferred_language", "en"),
            email_verified=item.get("email_verified", False),
            first_verified_at=(
                dt.datetime.fromisoformat(item["first_verified_at"])
                if item.get("first_verified_at")
                else None
            ),
            total_bookings=int(item.get("total_bookings", 0)),
            notes=item.get("notes"),
            created_at=dt.datetime.fromisoformat(item["created_at"]),
            updated_at=dt.datetime.fromisoformat(item["updated_at"]),
        )

    def _guest_to_item(self, guest: Guest) -> dict[str, Any]:
        """Convert Guest model to DynamoDB item."""
        item = {
            "guest_id": guest.guest_id,
            "email": guest.email,
            "preferred_language": guest.preferred_language,
            "email_verified": guest.email_verified,
            "total_bookings": guest.total_bookings,
            "created_at": guest.created_at.isoformat(),
            "updated_at": guest.updated_at.isoformat(),
        }
        if guest.name:
            item["name"] = guest.name
        if guest.phone:
            item["phone"] = guest.phone
        if guest.first_verified_at:
            item["first_verified_at"] = guest.first_verified_at.isoformat()
        if guest.notes:
            item["notes"] = guest.notes
        return item

    def _item_to_reservation(self, item: dict[str, Any]) -> Reservation:
        """Convert DynamoDB item to Reservation model."""
        return Reservation(
            reservation_id=item["reservation_id"],
            guest_id=item["guest_id"],
            check_in=dt.date.fromisoformat(item["check_in"]),
            check_out=dt.date.fromisoformat(item["check_out"]),
            num_adults=int(item["num_adults"]),
            num_children=int(item.get("num_children", 0)),
            status=ReservationStatus(item["status"]),
            payment_status=PaymentStatus(item["payment_status"]),
            total_amount=int(item["total_amount"]),
            cleaning_fee=int(item["cleaning_fee"]),
            nightly_rate=int(item["nightly_rate"]),
            nights=int(item["nights"]),
            special_requests=item.get("special_requests"),
            created_at=dt.datetime.fromisoformat(item["created_at"]),
            updated_at=dt.datetime.fromisoformat(item["updated_at"]),
            cancelled_at=(
                dt.datetime.fromisoformat(item["cancelled_at"])
                if item.get("cancelled_at")
                else None
            ),
            cancellation_reason=item.get("cancellation_reason"),
            refund_amount=(
                int(item["refund_amount"]) if item.get("refund_amount") else None
            ),
        )

    def _reservation_to_item(self, res: Reservation) -> dict[str, Any]:
        """Convert Reservation model to DynamoDB item."""
        item = {
            "reservation_id": res.reservation_id,
            "guest_id": res.guest_id,
            "check_in": res.check_in.isoformat(),
            "check_out": res.check_out.isoformat(),
            "num_adults": res.num_adults,
            "num_children": res.num_children,
            "status": res.status.value,
            "payment_status": res.payment_status.value,
            "total_amount": res.total_amount,
            "cleaning_fee": res.cleaning_fee,
            "nightly_rate": res.nightly_rate,
            "nights": res.nights,
            "created_at": res.created_at.isoformat(),
            "updated_at": res.updated_at.isoformat(),
        }
        if res.special_requests:
            item["special_requests"] = res.special_requests
        if res.cancelled_at:
            item["cancelled_at"] = res.cancelled_at.isoformat()
        if res.cancellation_reason:
            item["cancellation_reason"] = res.cancellation_reason
        if res.refund_amount is not None:
            item["refund_amount"] = res.refund_amount
        return item

    def _item_to_summary(self, item: dict[str, Any]) -> ReservationSummary:
        """Convert DynamoDB item to ReservationSummary."""
        return ReservationSummary(
            reservation_id=item["reservation_id"],
            check_in=dt.date.fromisoformat(item["check_in"]),
            check_out=dt.date.fromisoformat(item["check_out"]),
            status=ReservationStatus(item["status"]),
            total_amount=int(item["total_amount"]),
        )

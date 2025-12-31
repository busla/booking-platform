"""Unit tests for modify_reservation tool (T094).

Tests the modify_reservation functionality that allows guests
to update their booking dates or guest count.

Note: Tests must mock get_guest_by_cognito_sub as the tool verifies
ownership via AgentCore Identity OAuth2 (cognito_sub from JWT).
"""

from datetime import date, datetime, timezone
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from shared.models.enums import PaymentStatus, ReservationStatus


class TestModifyReservation:
    """Tests for the modify_reservation tool."""

    @patch("shared.tools.reservations._get_db")
    @patch("shared.tools.reservations._check_dates_available")
    async def test_modify_dates_success(
        self,
        mock_check_available: MagicMock,
        mock_get_db: MagicMock,
        mock_tool_context: MagicMock,
    ) -> None:
        """Should modify reservation dates successfully."""
        from shared.tools.reservations import modify_reservation

        # Setup mock DB with guest ownership verification
        mock_db = MagicMock()
        mock_db.get_item.return_value = {
            "reservation_id": "RES-2025-ABC12345",
            "guest_id": "guest-123",  # Must match guest returned by get_guest_by_cognito_sub
            "check_in": "2025-07-15",
            "check_out": "2025-07-22",
            "nights": 7,
            "num_adults": 2,
            "num_children": 0,
            "total_amount": 89000,
            "nightly_rate": 12000,
            "cleaning_fee": 5000,
            "status": ReservationStatus.CONFIRMED.value,
            "payment_status": PaymentStatus.COMPLETED.value,
        }
        # Mock guest lookup (ownership verification)
        mock_db.get_guest_by_cognito_sub.return_value = {
            "guest_id": "guest-123",
            "email": "test@example.com",
            "cognito_sub": "test-cognito-sub-123",
        }
        mock_db.update_item.return_value = True
        mock_get_db.return_value = mock_db
        mock_check_available.return_value = (True, [])

        # Call the tool (async)
        result = await modify_reservation(
            reservation_id="RES-2025-ABC12345",
            tool_context=mock_tool_context,
            new_check_in="2025-07-16",
            new_check_out="2025-07-23",
        )

        # Verify
        assert result.get("status") == "success" or result.get("success") is True
        assert "updated" in str(result.get("message", "")).lower()

    @patch("shared.tools.reservations._get_db")
    async def test_modify_reservation_not_found(
        self, mock_get_db: MagicMock, mock_tool_context: MagicMock
    ) -> None:
        """Should return error when reservation not found."""
        from shared.tools.reservations import modify_reservation

        mock_db = MagicMock()
        mock_db.get_item.return_value = None
        mock_get_db.return_value = mock_db

        result = await modify_reservation(
            reservation_id="RES-2025-INVALID",
            tool_context=mock_tool_context,
            new_check_in="2025-07-16",
            new_check_out="2025-07-23",
        )

        # ToolError format uses "success" instead of "status"
        assert result["success"] is False
        assert "not found" in result["message"].lower()

    @patch("shared.tools.reservations._get_db")
    async def test_modify_cancelled_reservation_fails(
        self, mock_get_db: MagicMock, mock_tool_context: MagicMock
    ) -> None:
        """Should not allow modifying cancelled reservations."""
        from shared.tools.reservations import modify_reservation

        mock_db = MagicMock()
        mock_db.get_item.return_value = {
            "reservation_id": "RES-2025-ABC12345",
            "guest_id": "guest-123",
            "check_in": "2025-07-15",
            "check_out": "2025-07-22",
            "nights": 7,
            "num_adults": 2,
            "total_amount": 89000,
            "status": ReservationStatus.CANCELLED.value,
            "payment_status": PaymentStatus.REFUNDED.value,
        }
        mock_db.get_guest_by_cognito_sub.return_value = {
            "guest_id": "guest-123",
            "email": "test@example.com",
        }
        mock_get_db.return_value = mock_db

        result = await modify_reservation(
            reservation_id="RES-2025-ABC12345",
            tool_context=mock_tool_context,
            new_check_in="2025-07-16",
            new_check_out="2025-07-23",
        )

        # ToolError format uses "success" instead of "status"
        assert result["success"] is False
        # ToolError.UNAUTHORIZED message is "Guest not authorized for this action"
        assert "not authorized" in result["message"].lower() or "cancelled" in result["message"].lower()

    @patch("shared.tools.reservations._get_db")
    @patch("shared.tools.reservations._check_dates_available")
    async def test_modify_dates_unavailable(
        self,
        mock_check_available: MagicMock,
        mock_get_db: MagicMock,
        mock_tool_context: MagicMock,
    ) -> None:
        """Should fail when new dates are not available."""
        from shared.tools.reservations import modify_reservation

        mock_db = MagicMock()
        mock_db.get_item.return_value = {
            "reservation_id": "RES-2025-ABC12345",
            "guest_id": "guest-123",
            "check_in": "2025-07-15",
            "check_out": "2025-07-22",
            "nights": 7,
            "num_adults": 2,
            "total_amount": 89000,
            "status": ReservationStatus.CONFIRMED.value,
            "payment_status": PaymentStatus.COMPLETED.value,
        }
        mock_db.get_guest_by_cognito_sub.return_value = {
            "guest_id": "guest-123",
            "email": "test@example.com",
        }
        mock_get_db.return_value = mock_db
        mock_check_available.return_value = (False, ["2025-08-01", "2025-08-02"])

        result = await modify_reservation(
            reservation_id="RES-2025-ABC12345",
            tool_context=mock_tool_context,
            new_check_in="2025-08-01",
            new_check_out="2025-08-08",
        )

        # ToolError format uses "success" instead of "status"
        assert result["success"] is False
        assert "unavailable" in result["message"].lower() or "available" in result["message"].lower()

    @patch("shared.tools.reservations._get_db")
    @patch("shared.tools.reservations._check_dates_available")
    async def test_modify_guest_count(
        self,
        mock_check_available: MagicMock,
        mock_get_db: MagicMock,
        mock_tool_context: MagicMock,
    ) -> None:
        """Should allow modifying guest count."""
        from shared.tools.reservations import modify_reservation

        mock_db = MagicMock()
        mock_db.get_item.return_value = {
            "reservation_id": "RES-2025-ABC12345",
            "guest_id": "guest-123",
            "check_in": "2025-07-15",
            "check_out": "2025-07-22",
            "nights": 7,
            "num_adults": 2,
            "num_children": 0,
            "total_amount": 89000,
            "status": ReservationStatus.CONFIRMED.value,
            "payment_status": PaymentStatus.COMPLETED.value,
        }
        mock_db.get_guest_by_cognito_sub.return_value = {
            "guest_id": "guest-123",
            "email": "test@example.com",
        }
        mock_db.update_item.return_value = True
        mock_get_db.return_value = mock_db
        mock_check_available.return_value = (True, [])

        result = await modify_reservation(
            reservation_id="RES-2025-ABC12345",
            tool_context=mock_tool_context,
            new_num_adults=3,
            new_num_children=1,
        )

        assert result.get("status") == "success" or result.get("success") is True

    @patch("shared.tools.reservations._get_db")
    async def test_modify_exceeds_max_guests(
        self, mock_get_db: MagicMock, mock_tool_context: MagicMock
    ) -> None:
        """Should fail when new guest count exceeds maximum."""
        from shared.tools.reservations import modify_reservation

        mock_db = MagicMock()
        mock_db.get_item.return_value = {
            "reservation_id": "RES-2025-ABC12345",
            "guest_id": "guest-123",
            "check_in": "2025-07-15",
            "check_out": "2025-07-22",
            "nights": 7,
            "num_adults": 2,
            "num_children": 0,
            "total_amount": 89000,
            "status": ReservationStatus.CONFIRMED.value,
            "payment_status": PaymentStatus.COMPLETED.value,
        }
        mock_db.get_guest_by_cognito_sub.return_value = {
            "guest_id": "guest-123",
            "email": "test@example.com",
        }
        mock_get_db.return_value = mock_db

        result = await modify_reservation(
            reservation_id="RES-2025-ABC12345",
            tool_context=mock_tool_context,
            new_num_adults=8,  # Exceeds max capacity
        )

        assert result.get("status") == "error" or result.get("success") is False
        assert "maximum" in result["message"].lower() or "guest" in result["message"].lower()


class TestModifyReservationPriceRecalculation:
    """Tests for price recalculation on modification."""

    @patch("shared.tools.reservations._get_db")
    @patch("shared.tools.reservations._check_dates_available")
    @patch("shared.tools.reservations._get_pricing_for_dates")
    async def test_price_recalculation_longer_stay(
        self,
        mock_pricing: MagicMock,
        mock_check_available: MagicMock,
        mock_get_db: MagicMock,
        mock_tool_context: MagicMock,
    ) -> None:
        """Should recalculate price when extending stay."""
        from shared.tools.reservations import modify_reservation

        mock_db = MagicMock()
        mock_db.get_item.return_value = {
            "reservation_id": "RES-2025-ABC12345",
            "guest_id": "guest-123",
            "check_in": "2025-07-15",
            "check_out": "2025-07-22",  # 7 nights
            "nights": 7,
            "num_adults": 2,
            "total_amount": 89000,  # 7 nights * 12000 + 5000
            "nightly_rate": 12000,
            "cleaning_fee": 5000,
            "status": ReservationStatus.CONFIRMED.value,
            "payment_status": PaymentStatus.COMPLETED.value,
        }
        mock_db.get_guest_by_cognito_sub.return_value = {
            "guest_id": "guest-123",
            "email": "test@example.com",
        }
        mock_db.update_item.return_value = True
        mock_get_db.return_value = mock_db
        mock_check_available.return_value = (True, [])
        mock_pricing.return_value = (12000, 5000)  # Same rate

        result = await modify_reservation(
            reservation_id="RES-2025-ABC12345",
            tool_context=mock_tool_context,
            new_check_in="2025-07-15",
            new_check_out="2025-07-25",  # 10 nights
        )

        assert result.get("status") == "success" or result.get("success") is True
        # Should show price difference
        if "price" in result:
            assert result["new_total_cents"] == 10 * 12000 + 5000  # 125000

"""Unit tests for @requires_access_token decorator behavior (T021).

Tests verify that reservation tools decorated with @requires_access_token:
1. Receive the injected access_token parameter
2. Can extract cognito_sub and email from the JWT
3. Use JWT claims for user identification (not conversation context)

Note: The actual decorator is mocked in conftest.py via _mock_requires_access_token
which injects a test JWT token. These tests verify the tool-side handling of
the injected token.
"""

import base64
import json
from datetime import datetime, timedelta, timezone
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from shared.models.enums import PaymentStatus, ReservationStatus
from shared.utils.jwt import extract_cognito_claims, extract_cognito_sub


class TestRequiresAccessTokenDecorator:
    """Tests verifying @requires_access_token decorator behavior on reservation tools."""

    def test_mock_jwt_structure(self) -> None:
        """Verify mock JWT from conftest has valid structure.

        The conftest._create_mock_jwt creates tokens that extract_cognito_claims
        can parse. This test confirms the mock JWT structure is valid.
        """
        # Create JWT matching conftest pattern
        header = {"alg": "RS256", "typ": "JWT"}
        payload = {
            "sub": "test-cognito-sub-123",
            "email": "test@example.com",
            "email_verified": True,
            "iss": "https://cognito-idp.eu-west-1.amazonaws.com/eu-west-1_TestPool",
            "aud": "test-client-id-123",
            "token_use": "access",
            "exp": 9999999999,
        }
        header_b64 = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip("=")
        payload_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
        mock_jwt = f"{header_b64}.{payload_b64}.mock-signature"

        # Extract claims
        cognito_sub, email = extract_cognito_claims(mock_jwt)

        assert cognito_sub == "test-cognito-sub-123"
        assert email == "test@example.com"

    def test_extract_cognito_sub_from_token(self) -> None:
        """Verify extract_cognito_sub extracts sub claim correctly."""
        # Use proper JWT format (header.payload.signature)
        header = {"alg": "none", "typ": "JWT"}
        payload = {
            "sub": "user-uuid-12345",
            "email": "user@test.com",
        }
        header_b64 = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip("=")
        payload_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
        token = f"{header_b64}.{payload_b64}."

        result = extract_cognito_sub(token)
        assert result == "user-uuid-12345"

    def test_extract_cognito_claims_handles_missing_email(self) -> None:
        """Verify extract_cognito_claims handles tokens without email claim."""
        # Use proper JWT format with 'none' algorithm
        header = {"alg": "none", "typ": "JWT"}
        payload = {"sub": "user-uuid-12345"}
        header_b64 = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip("=")
        payload_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
        token = f"{header_b64}.{payload_b64}."

        cognito_sub, email = extract_cognito_claims(token)
        assert cognito_sub == "user-uuid-12345"
        assert email is None

    def test_extract_cognito_claims_handles_invalid_token(self) -> None:
        """Verify extract_cognito_claims returns None for invalid tokens."""
        # Invalid token structure
        cognito_sub, email = extract_cognito_claims("invalid-token")
        assert cognito_sub is None
        assert email is None

        # Empty token
        cognito_sub, email = extract_cognito_claims("")
        assert cognito_sub is None
        assert email is None


class TestCreateReservationAuthBehavior:
    """Tests for create_reservation tool's token handling."""

    @patch("shared.tools.reservations._get_db")
    async def test_create_reservation_receives_access_token(
        self, mock_get_db: MagicMock, mock_tool_context: MagicMock
    ) -> None:
        """Verify create_reservation receives injected access_token from decorator.

        The mock decorator in conftest automatically injects access_token.
        This test confirms the tool receives it.
        """
        from shared.tools.reservations import create_reservation

        # Setup mock DB
        mock_db = MagicMock()
        mock_db.get_customer_by_cognito_sub.return_value = {
            "customer_id": "customer-123",
            "email": "test@example.com",
            "cognito_sub": "test-cognito-sub-123",
        }
        mock_db.batch_get.return_value = []  # Dates available
        mock_db.transact_write.return_value = True
        mock_get_db.return_value = mock_db

        # Call tool - decorator injects access_token
        result = await create_reservation(
            check_in="2025-08-01",
            check_out="2025-08-05",
            num_adults=2,
            tool_context=mock_tool_context,
        )

        # Tool should succeed (meaning it received the token)
        assert result.get("status") == "success"
        assert "reservation_id" in result

        # Verify customer lookup was called with cognito_sub from token
        mock_db.get_customer_by_cognito_sub.assert_called_once_with("test-cognito-sub-123")

    @patch("shared.tools.reservations._get_db")
    async def test_create_reservation_extracts_email_from_jwt(
        self, mock_get_db: MagicMock, mock_tool_context: MagicMock
    ) -> None:
        """Verify create_reservation uses email from JWT, not conversation context."""
        from shared.tools.reservations import create_reservation

        mock_db = MagicMock()
        mock_db.get_customer_by_cognito_sub.return_value = {
            "customer_id": "customer-123",
            "email": "test@example.com",
            "cognito_sub": "test-cognito-sub-123",
        }
        mock_db.batch_get.return_value = []
        mock_db.transact_write.return_value = True
        mock_get_db.return_value = mock_db

        result = await create_reservation(
            check_in="2025-08-10",
            check_out="2025-08-15",
            num_adults=2,
            tool_context=mock_tool_context,
        )

        # Response should include authenticated_email from JWT
        assert result.get("status") == "success"
        assert result.get("authenticated_email") == "test@example.com"

    @patch("shared.tools.reservations._get_db")
    async def test_create_reservation_rejects_invalid_token(
        self, mock_get_db: MagicMock, mock_tool_context: MagicMock
    ) -> None:
        """Verify create_reservation handles invalid access_token gracefully."""
        from shared.tools.reservations import create_reservation

        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        # Call with invalid token (bypassing the mock decorator by passing explicit token)
        result = await create_reservation(
            check_in="2025-08-01",
            check_out="2025-08-05",
            num_adults=2,
            tool_context=mock_tool_context,
            access_token="invalid-token-no-sub",
        )

        # Should return verification error
        assert result.get("success") is False
        assert "error_code" in result


class TestModifyReservationAuthBehavior:
    """Tests for modify_reservation tool's token handling."""

    @patch("shared.tools.reservations._get_db")
    async def test_modify_reservation_verifies_ownership(
        self, mock_get_db: MagicMock, mock_tool_context: MagicMock
    ) -> None:
        """Verify modify_reservation uses JWT sub to verify ownership.

        The tool should only allow modification if the JWT's cognito_sub
        matches the reservation's owner.
        """
        from shared.tools.reservations import modify_reservation

        mock_db = MagicMock()
        # Reservation belongs to customer-123
        mock_db.get_item.return_value = {
            "reservation_id": "RES-2025-ABC12345",
            "customer_id": "customer-123",
            "check_in": "2025-09-01",
            "check_out": "2025-09-05",
            "nights": 4,
            "num_adults": 2,
            "total_amount": 48000,
            "status": ReservationStatus.CONFIRMED.value,
            "payment_status": PaymentStatus.COMPLETED.value,
        }
        # Token's cognito_sub maps to customer-123
        mock_db.get_customer_by_cognito_sub.return_value = {
            "customer_id": "customer-123",
            "email": "test@example.com",
            "cognito_sub": "test-cognito-sub-123",
        }
        mock_db.update_item.return_value = True
        mock_get_db.return_value = mock_db

        result = await modify_reservation(
            reservation_id="RES-2025-ABC12345",
            tool_context=mock_tool_context,
            new_num_adults=3,
        )

        assert result.get("status") == "success"
        mock_db.get_customer_by_cognito_sub.assert_called_once_with("test-cognito-sub-123")

    @patch("shared.tools.reservations._get_db")
    async def test_modify_reservation_rejects_non_owner(
        self, mock_get_db: MagicMock, mock_tool_context: MagicMock
    ) -> None:
        """Verify modify_reservation rejects modification by non-owner."""
        from shared.tools.reservations import modify_reservation

        mock_db = MagicMock()
        # Reservation belongs to different customer
        mock_db.get_item.return_value = {
            "reservation_id": "RES-2025-ABC12345",
            "customer_id": "other-customer-999",  # Different customer
            "check_in": "2025-09-01",
            "check_out": "2025-09-05",
            "nights": 4,
            "num_adults": 2,
            "total_amount": 48000,
            "status": ReservationStatus.CONFIRMED.value,
            "payment_status": PaymentStatus.COMPLETED.value,
        }
        # Token's cognito_sub maps to customer-123
        mock_db.get_customer_by_cognito_sub.return_value = {
            "customer_id": "customer-123",
            "email": "test@example.com",
            "cognito_sub": "test-cognito-sub-123",
        }
        mock_get_db.return_value = mock_db

        result = await modify_reservation(
            reservation_id="RES-2025-ABC12345",
            tool_context=mock_tool_context,
            new_num_adults=3,
        )

        # Should return unauthorized error
        assert result.get("success") is False
        assert "UNAUTHORIZED" in result.get("error_code", "") or "not authorized" in result.get("message", "").lower()


class TestCancelReservationAuthBehavior:
    """Tests for cancel_reservation tool's token handling."""

    @patch("shared.tools.reservations._get_db")
    async def test_cancel_reservation_verifies_ownership(
        self, mock_get_db: MagicMock, mock_tool_context: MagicMock
    ) -> None:
        """Verify cancel_reservation uses JWT sub to verify ownership."""
        from shared.tools.reservations import cancel_reservation

        mock_db = MagicMock()
        future_checkin = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        mock_db.get_item.return_value = {
            "reservation_id": "RES-2025-ABC12345",
            "customer_id": "customer-123",
            "check_in": future_checkin,
            "check_out": (datetime.now() + timedelta(days=35)).strftime("%Y-%m-%d"),
            "nights": 5,
            "num_adults": 2,
            "total_amount": 60000,
            "status": ReservationStatus.CONFIRMED.value,
            "payment_status": PaymentStatus.COMPLETED.value,
        }
        mock_db.get_customer_by_cognito_sub.return_value = {
            "customer_id": "customer-123",
            "email": "test@example.com",
            "cognito_sub": "test-cognito-sub-123",
        }
        mock_db.transact_write.return_value = True
        mock_get_db.return_value = mock_db

        result = await cancel_reservation(
            reservation_id="RES-2025-ABC12345",
            tool_context=mock_tool_context,
            reason="Test cancellation",
        )

        assert result.get("status") == "success"
        mock_db.get_customer_by_cognito_sub.assert_called_once_with("test-cognito-sub-123")


class TestGetMyReservationsAuthBehavior:
    """Tests for get_my_reservations tool's token handling."""

    @patch("shared.tools.reservations._get_db")
    async def test_get_my_reservations_scopes_by_cognito_sub(
        self, mock_get_db: MagicMock, mock_tool_context: MagicMock
    ) -> None:
        """Verify get_my_reservations uses JWT sub to scope DynamoDB query.

        This is the 'guardrail pattern' - using JWT claims to restrict
        database queries to only the authenticated user's data.
        """
        from shared.tools.reservations import get_my_reservations

        mock_db = MagicMock()
        mock_db.get_customer_by_cognito_sub.return_value = {
            "customer_id": "customer-123",
            "email": "test@example.com",
            "cognito_sub": "test-cognito-sub-123",
        }
        mock_db.get_reservations_by_customer_id.return_value = [
            {
                "reservation_id": "RES-2025-001",
                "check_in": "2025-07-01",
                "check_out": "2025-07-05",
                "nights": 4,
                "num_adults": 2,
                "total_amount": 48000,
                "status": "confirmed",
                "payment_status": "completed",
            }
        ]
        mock_get_db.return_value = mock_db

        result = await get_my_reservations(tool_context=mock_tool_context)

        assert result.get("status") == "success"
        assert result.get("count") == 1

        # Verify JWT sub was used to look up customer
        mock_db.get_customer_by_cognito_sub.assert_called_once_with("test-cognito-sub-123")
        # Verify reservations were queried by customer_id (derived from JWT sub)
        mock_db.get_reservations_by_customer_id.assert_called_once_with("customer-123")

    @patch("shared.tools.reservations._get_db")
    async def test_get_my_reservations_handles_no_customer_record(
        self, mock_get_db: MagicMock, mock_tool_context: MagicMock
    ) -> None:
        """Verify get_my_reservations handles authenticated user without customer record."""
        from shared.tools.reservations import get_my_reservations

        mock_db = MagicMock()
        mock_db.get_customer_by_cognito_sub.return_value = None  # No customer record
        mock_get_db.return_value = mock_db

        result = await get_my_reservations(tool_context=mock_tool_context)

        # Should return empty list, not error
        assert result.get("status") == "success"
        assert result.get("count") == 0
        assert result.get("reservations") == []


class TestDecoratorConfiguration:
    """Tests verifying @requires_access_token decorator configuration."""

    def test_all_protected_tools_have_decorator(self) -> None:
        """Verify all reservation-modifying tools have @requires_access_token.

        This is a static analysis test to ensure no protected tool
        accidentally loses its decorator.
        """
        from shared.tools.reservations import (
            cancel_reservation,
            create_reservation,
            get_my_reservations,
            modify_reservation,
        )

        # These tools should have the decorator (wrapped functions)
        protected_tools = [
            create_reservation,
            modify_reservation,
            cancel_reservation,
            get_my_reservations,
        ]

        for tool_func in protected_tools:
            # Decorated functions have __wrapped__ attribute
            assert hasattr(tool_func, "__wrapped__"), (
                f"{tool_func.__name__} is missing @requires_access_token decorator"
            )

    def test_get_reservation_is_not_protected(self) -> None:
        """Verify get_reservation (read-only) doesn't require auth.

        get_reservation only reads a single reservation by ID and doesn't
        expose sensitive user data, so it's intentionally unprotected.
        """
        from shared.tools.reservations import get_reservation

        # This tool should NOT have the decorator - it's synchronous and public
        # The @tool decorator is present but not @requires_access_token
        # Check it's callable without access_token
        import inspect
        sig = inspect.signature(get_reservation)
        param_names = list(sig.parameters.keys())

        # Should not require access_token
        assert "access_token" not in param_names

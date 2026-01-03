"""Integration tests for returning user authentication flow (T042).

Tests User Story 5: Returning users with valid tokens don't need to re-authenticate.

The @requires_access_token decorator is mocked in conftest.py to inject a test JWT.
These tests verify that:
1. Multiple consecutive calls to protected tools work with the same token
2. The JWT claims are correctly extracted for all calls
3. User data isolation is maintained across multiple calls

Note: The actual AgentCore TokenVault behavior (caching tokens after CompleteResourceTokenAuth)
is handled by the AWS service. These tests validate the tool-side behavior when a token
is already available.
"""

import os
from datetime import date, timedelta
from typing import Any, Generator
from unittest.mock import MagicMock, patch

import boto3
import pytest
from moto import mock_aws


# === Dynamic Date Helpers ===


def _base_date() -> date:
    """Get a base date 60 days in the future for testing."""
    return date.today() + timedelta(days=60)


def _date_str(offset: int = 0) -> str:
    """Get a date string offset from the base date."""
    return (_base_date() + timedelta(days=offset)).isoformat()


# === Fixtures ===


@pytest.fixture
def aws_credentials() -> Generator[None, None, None]:
    """Mocked AWS Credentials for moto."""
    original_values = {
        key: os.environ.get(key)
        for key in [
            "AWS_ACCESS_KEY_ID",
            "AWS_SECRET_ACCESS_KEY",
            "AWS_SECURITY_TOKEN",
            "AWS_SESSION_TOKEN",
        ]
    }

    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "eu-west-1"

    yield

    for key, value in original_values.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value


@pytest.fixture
def dynamodb_tables(aws_credentials: None) -> Generator[Any, None, None]:
    """Create all required DynamoDB tables.

    Table setup mirrors test_booking_flow.py to ensure consistency.
    """
    with mock_aws():
        dynamodb = boto3.client("dynamodb", region_name="eu-west-1")

        # Create reservations table with GSI for customer_id lookup
        dynamodb.create_table(
            TableName="test-booking-reservations",
            KeySchema=[{"AttributeName": "reservation_id", "KeyType": "HASH"}],
            AttributeDefinitions=[
                {"AttributeName": "reservation_id", "AttributeType": "S"},
                {"AttributeName": "customer_id", "AttributeType": "S"},
            ],
            GlobalSecondaryIndexes=[
                {
                    "IndexName": "customer-checkin-index",
                    "KeySchema": [{"AttributeName": "customer_id", "KeyType": "HASH"}],
                    "Projection": {"ProjectionType": "ALL"},
                }
            ],
            BillingMode="PAY_PER_REQUEST",
        )

        # Create customers table with GSIs for email and cognito_sub lookup
        dynamodb.create_table(
            TableName="test-booking-customers",
            KeySchema=[{"AttributeName": "customer_id", "KeyType": "HASH"}],
            AttributeDefinitions=[
                {"AttributeName": "customer_id", "AttributeType": "S"},
                {"AttributeName": "email", "AttributeType": "S"},
                {"AttributeName": "cognito_sub", "AttributeType": "S"},
            ],
            GlobalSecondaryIndexes=[
                {
                    "IndexName": "email-index",
                    "KeySchema": [{"AttributeName": "email", "KeyType": "HASH"}],
                    "Projection": {"ProjectionType": "ALL"},
                },
                {
                    "IndexName": "cognito-sub-index",
                    "KeySchema": [{"AttributeName": "cognito_sub", "KeyType": "HASH"}],
                    "Projection": {"ProjectionType": "ALL"},
                },
            ],
            BillingMode="PAY_PER_REQUEST",
        )

        # Create availability table
        dynamodb.create_table(
            TableName="test-booking-availability",
            KeySchema=[{"AttributeName": "date", "KeyType": "HASH"}],
            AttributeDefinitions=[
                {"AttributeName": "date", "AttributeType": "S"},
            ],
            BillingMode="PAY_PER_REQUEST",
        )

        # Create pricing table (uses 'season' not 'season_id' per existing tests)
        dynamodb.create_table(
            TableName="test-booking-pricing",
            KeySchema=[{"AttributeName": "season", "KeyType": "HASH"}],
            AttributeDefinitions=[
                {"AttributeName": "season", "AttributeType": "S"},
            ],
            BillingMode="PAY_PER_REQUEST",
        )

        yield dynamodb


@pytest.fixture
def seed_customer(dynamodb_tables: Any) -> dict[str, Any]:
    """Seed a test customer that matches the mock JWT from conftest.py.

    The mock JWT has cognito_sub="test-cognito-sub-123".
    """
    dynamodb = boto3.resource("dynamodb", region_name="eu-west-1")
    table = dynamodb.Table("test-booking-customers")

    customer = {
        "customer_id": "customer-returning-user-001",
        "email": "test@example.com",
        "name": "Test User",
        "cognito_sub": "test-cognito-sub-123",  # Must match conftest mock JWT
        "created_at": "2025-01-01T00:00:00Z",
    }

    table.put_item(Item=customer)
    return customer


@pytest.fixture
def seed_available_dates(dynamodb_tables: Any) -> list[str]:
    """Seed available dates for testing.

    Uses 'status: available' format per check_availability tool expectations.
    """
    dynamodb = boto3.resource("dynamodb", region_name="eu-west-1")
    table = dynamodb.Table("test-booking-availability")

    dates = []
    for offset in range(20):  # Seed 20 days to cover all test scenarios
        date_str = _date_str(offset)
        dates.append(date_str)
        table.put_item(
            Item={
                "date": date_str,
                "status": "available",  # Matches check_availability expectations
                "reservation_id": None,
            }
        )

    return dates


@pytest.fixture
def mock_tool_context() -> MagicMock:
    """Create a mock tool context for testing."""
    context = MagicMock()
    context.session_id = "test-session-returning-user"
    return context


# === Tests ===


class TestReturningUserTokenReuse:
    """Tests verifying token reuse for returning users.

    These tests simulate a returning user who has already authenticated.
    The @requires_access_token decorator (mocked in conftest) injects the same
    JWT token for all calls, simulating the AgentCore TokenVault behavior.
    """

    @pytest.mark.asyncio
    async def test_multiple_reservation_queries_same_token(
        self,
        dynamodb_tables: Any,
        seed_customer: dict[str, Any],
        mock_tool_context: MagicMock,
    ) -> None:
        """Verify multiple calls to get_my_reservations work with same token.

        Simulates: User returns, makes several queries about their reservations.
        Expected: All queries succeed without re-authentication prompts.
        """
        from shared.tools.reservations import get_my_reservations

        # First call
        result1 = await get_my_reservations(tool_context=mock_tool_context)
        assert result1.get("status") == "success"
        assert result1.get("count") == 0  # No reservations yet

        # Second call (simulates user asking again)
        result2 = await get_my_reservations(tool_context=mock_tool_context)
        assert result2.get("status") == "success"

        # Third call
        result3 = await get_my_reservations(tool_context=mock_tool_context)
        assert result3.get("status") == "success"

        # All calls should succeed - no auth_required responses
        for result in [result1, result2, result3]:
            assert result.get("status") != "auth_required"

    @pytest.mark.asyncio
    async def test_create_then_retrieve_reservations(
        self,
        dynamodb_tables: Any,
        seed_customer: dict[str, Any],
        seed_available_dates: list[str],
        mock_tool_context: MagicMock,
    ) -> None:
        """Verify create + retrieve works with same token session.

        Simulates: User creates a reservation, then queries their reservations.
        Expected: Both operations succeed with the same authenticated session.
        """
        from shared.tools.reservations import create_reservation, get_my_reservations

        check_in = _date_str(0)
        check_out = _date_str(4)

        # Create reservation
        create_result = await create_reservation(
            check_in=check_in,
            check_out=check_out,
            num_adults=2,
            tool_context=mock_tool_context,
        )

        assert create_result.get("status") == "success"
        reservation_id = create_result.get("reservation_id")
        assert reservation_id is not None

        # Retrieve reservations (same token session)
        list_result = await get_my_reservations(tool_context=mock_tool_context)

        assert list_result.get("status") == "success"
        assert list_result.get("count") == 1
        reservations = list_result.get("reservations", [])
        assert len(reservations) == 1
        assert reservations[0].get("reservation_id") == reservation_id

    @pytest.mark.asyncio
    async def test_modify_own_reservation_with_cached_token(
        self,
        dynamodb_tables: Any,
        seed_customer: dict[str, Any],
        seed_available_dates: list[str],
        mock_tool_context: MagicMock,
    ) -> None:
        """Verify modify works with same token session.

        Simulates: User creates reservation, returns later to modify it.
        Expected: Modification succeeds because token is still valid.
        """
        from shared.tools.reservations import create_reservation, modify_reservation

        check_in = _date_str(0)
        check_out = _date_str(3)

        # Create reservation
        create_result = await create_reservation(
            check_in=check_in,
            check_out=check_out,
            num_adults=2,
            tool_context=mock_tool_context,
        )

        assert create_result.get("status") == "success"
        reservation_id = create_result.get("reservation_id")

        # Modify reservation (same token session)
        modify_result = await modify_reservation(
            reservation_id=reservation_id,
            new_num_adults=3,
            tool_context=mock_tool_context,
        )

        assert modify_result.get("status") == "success"
        # num_adults is returned at top level, not in updated_fields
        assert modify_result.get("num_adults") == 3


class TestJWTClaimExtraction:
    """Tests verifying JWT claims are correctly extracted on each call."""

    @pytest.mark.asyncio
    async def test_email_extracted_from_token_consistently(
        self,
        dynamodb_tables: Any,
        seed_customer: dict[str, Any],
        seed_available_dates: list[str],
        mock_tool_context: MagicMock,
    ) -> None:
        """Verify email claim is extracted from JWT consistently.

        The authenticated_email in response should match the JWT email claim.
        """
        from shared.tools.reservations import create_reservation

        result = await create_reservation(
            check_in=_date_str(0),
            check_out=_date_str(2),
            num_adults=2,
            tool_context=mock_tool_context,
        )

        assert result.get("status") == "success"
        # authenticated_email is set from JWT claim, not from request
        assert result.get("authenticated_email") == "test@example.com"

    @pytest.mark.asyncio
    async def test_cognito_sub_used_for_customer_lookup(
        self,
        dynamodb_tables: Any,
        seed_customer: dict[str, Any],
        mock_tool_context: MagicMock,
    ) -> None:
        """Verify cognito_sub from JWT is used to look up customer.

        The tool should use the JWT sub claim to find the customer record,
        ensuring proper data isolation.
        """
        from shared.tools.reservations import get_my_reservations

        result = await get_my_reservations(tool_context=mock_tool_context)

        assert result.get("status") == "success"
        # The fact that this succeeds means cognito_sub lookup worked
        # (seed_customer has cognito_sub="test-cognito-sub-123")


class TestDataIsolation:
    """Tests verifying user data isolation with returning user scenario."""

    @pytest.mark.asyncio
    async def test_cannot_see_other_user_reservations(
        self,
        dynamodb_tables: Any,
        seed_customer: dict[str, Any],
        mock_tool_context: MagicMock,
    ) -> None:
        """Verify user cannot see reservations belonging to other users.

        Even with a valid token, user should only see their own data.
        """
        # Create a reservation for a DIFFERENT customer
        dynamodb = boto3.resource("dynamodb", region_name="eu-west-1")

        # Create another customer
        customers_table = dynamodb.Table("test-booking-customers")
        customers_table.put_item(
            Item={
                "customer_id": "customer-other-user-999",
                "email": "other@example.com",
                "name": "Other User",
                "cognito_sub": "other-cognito-sub-999",  # Different from mock JWT
                "created_at": "2025-01-01T00:00:00Z",
            }
        )

        # Create reservation for other customer
        reservations_table = dynamodb.Table("test-booking-reservations")
        reservations_table.put_item(
            Item={
                "reservation_id": "RES-OTHER-001",
                "customer_id": "customer-other-user-999",
                "check_in": _date_str(0),
                "check_out": _date_str(3),
                "nights": 3,
                "num_adults": 2,
                "status": "confirmed",
                "total_amount": 45000,
                "created_at": "2025-01-01T00:00:00Z",
            }
        )

        from shared.tools.reservations import get_my_reservations

        # Query with test user token (cognito_sub="test-cognito-sub-123")
        result = await get_my_reservations(tool_context=mock_tool_context)

        # Should return 0 reservations (test customer has none)
        # NOT the other customer's reservation
        assert result.get("status") == "success"
        assert result.get("count") == 0
        assert result.get("reservations") == []

    @pytest.mark.asyncio
    async def test_cannot_modify_other_user_reservation(
        self,
        dynamodb_tables: Any,
        seed_customer: dict[str, Any],
        mock_tool_context: MagicMock,
    ) -> None:
        """Verify user cannot modify reservations belonging to other users."""
        # Create another customer and their reservation
        dynamodb = boto3.resource("dynamodb", region_name="eu-west-1")

        customers_table = dynamodb.Table("test-booking-customers")
        customers_table.put_item(
            Item={
                "customer_id": "customer-other-user-888",
                "email": "other2@example.com",
                "cognito_sub": "other-cognito-sub-888",
            }
        )

        reservations_table = dynamodb.Table("test-booking-reservations")
        reservations_table.put_item(
            Item={
                "reservation_id": "RES-OTHER-002",
                "customer_id": "customer-other-user-888",
                "check_in": _date_str(10),
                "check_out": _date_str(13),
                "nights": 3,
                "num_adults": 2,
                "status": "confirmed",
                "payment_status": "completed",
                "total_amount": 45000,
                "created_at": "2025-01-01T00:00:00Z",
            }
        )

        from shared.tools.reservations import modify_reservation

        # Try to modify other user's reservation
        result = await modify_reservation(
            reservation_id="RES-OTHER-002",
            new_num_adults=4,
            tool_context=mock_tool_context,
        )

        # Should be rejected (unauthorized)
        assert result.get("success") is False
        error_code = result.get("error_code", "")
        # Could be ERR_007 (UNAUTHORIZED) or contain "not authorized"
        assert "UNAUTHORIZED" in str(error_code) or "not authorized" in result.get("message", "").lower()

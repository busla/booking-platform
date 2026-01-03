"""Integration tests for DynamoDB cognito-sub-index GSI queries (T007a).

TDD Red Phase: Tests define expected behavior for get_customer_by_cognito_sub().

Tests verify:
- GSI query returns correct customer when cognito_sub exists
- GSI query returns None when cognito_sub doesn't exist
- Multiple customers with different cognito_subs are correctly distinguished
"""

from datetime import datetime, timezone
from typing import Any
from unittest.mock import patch

import pytest
from moto import mock_aws

from shared.services.dynamodb import DynamoDBService, reset_dynamodb_service


@pytest.fixture
def dynamodb_service(create_tables: None) -> DynamoDBService:
    """Create DynamoDB service instance within moto mock context.

    The create_tables fixture (from conftest.py) sets up the mock DynamoDB
    tables including the customers table with cognito-sub-index GSI.
    """
    # Reset singleton to ensure fresh instance within mock context
    reset_dynamodb_service()
    return DynamoDBService()


@pytest.fixture
def sample_customer_with_cognito_sub() -> dict[str, Any]:
    """Sample customer data with cognito_sub for testing GSI queries."""
    return {
        "customer_id": "customer-cognito-test-001",
        "email": "cognito-test@example.com",
        "full_name": "Cognito Test User",
        "phone": "+34 612 345 678",
        "preferred_language": "en",
        "cognito_sub": "cognito-sub-12345-abcdef",
        "email_verified": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "reservation_count": 0,
    }


@pytest.fixture
def second_customer_with_cognito_sub() -> dict[str, Any]:
    """Second customer with different cognito_sub for distinguishing queries."""
    return {
        "customer_id": "customer-cognito-test-002",
        "email": "second-cognito@example.com",
        "full_name": "Second Cognito User",
        "phone": "+34 698 765 432",
        "preferred_language": "es",
        "cognito_sub": "cognito-sub-67890-ghijkl",
        "email_verified": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "reservation_count": 2,
    }


class TestGetCustomerByCognitoSub:
    """Test suite for get_customer_by_cognito_sub() method."""

    @mock_aws
    def test_returns_customer_when_cognito_sub_exists(
        self,
        dynamodb_service: DynamoDBService,
        sample_customer_with_cognito_sub: dict[str, Any],
    ) -> None:
        """get_customer_by_cognito_sub returns correct customer when cognito_sub exists."""
        # Arrange: Insert customer into DynamoDB
        dynamodb_service.put_item("customers", sample_customer_with_cognito_sub)

        # Act: Query by cognito_sub via GSI
        result = dynamodb_service.get_customer_by_cognito_sub("cognito-sub-12345-abcdef")

        # Assert: Correct customer is returned
        assert result is not None
        assert result["customer_id"] == "customer-cognito-test-001"
        assert result["email"] == "cognito-test@example.com"
        assert result["cognito_sub"] == "cognito-sub-12345-abcdef"
        assert result["full_name"] == "Cognito Test User"

    @mock_aws
    def test_returns_none_when_cognito_sub_not_found(
        self,
        dynamodb_service: DynamoDBService,
    ) -> None:
        """get_customer_by_cognito_sub returns None when cognito_sub doesn't exist."""
        # Act: Query for non-existent cognito_sub
        result = dynamodb_service.get_customer_by_cognito_sub("nonexistent-cognito-sub")

        # Assert: None is returned, not an exception
        assert result is None

    @mock_aws
    def test_distinguishes_between_multiple_customers(
        self,
        dynamodb_service: DynamoDBService,
        sample_customer_with_cognito_sub: dict[str, Any],
        second_customer_with_cognito_sub: dict[str, Any],
    ) -> None:
        """get_customer_by_cognito_sub returns correct customer among multiple."""
        # Arrange: Insert both customers
        dynamodb_service.put_item("customers", sample_customer_with_cognito_sub)
        dynamodb_service.put_item("customers", second_customer_with_cognito_sub)

        # Act: Query for second customer's cognito_sub
        result = dynamodb_service.get_customer_by_cognito_sub("cognito-sub-67890-ghijkl")

        # Assert: Returns the correct customer (second one)
        assert result is not None
        assert result["customer_id"] == "customer-cognito-test-002"
        assert result["email"] == "second-cognito@example.com"
        assert result["cognito_sub"] == "cognito-sub-67890-ghijkl"
        assert result["full_name"] == "Second Cognito User"

    @mock_aws
    def test_raises_error_for_empty_cognito_sub_string(
        self,
        dynamodb_service: DynamoDBService,
        sample_customer_with_cognito_sub: dict[str, Any],
    ) -> None:
        """get_customer_by_cognito_sub raises ClientError for empty string query.

        DynamoDB does not allow empty strings as key attribute values.
        This is enforced at the API level with ValidationException.
        """
        from botocore.exceptions import ClientError

        # Arrange: Insert a customer with valid cognito_sub
        dynamodb_service.put_item("customers", sample_customer_with_cognito_sub)

        # Act & Assert: Query with empty string raises ValidationException
        with pytest.raises(ClientError) as exc_info:
            dynamodb_service.get_customer_by_cognito_sub("")

        assert "ValidationException" in str(exc_info.value)
        assert "empty string" in str(exc_info.value).lower()

    @mock_aws
    def test_returns_all_customer_fields(
        self,
        dynamodb_service: DynamoDBService,
        sample_customer_with_cognito_sub: dict[str, Any],
    ) -> None:
        """get_customer_by_cognito_sub returns all customer fields (ProjectionType: ALL)."""
        # Arrange: Insert customer with all fields
        dynamodb_service.put_item("customers", sample_customer_with_cognito_sub)

        # Act: Query by cognito_sub
        result = dynamodb_service.get_customer_by_cognito_sub("cognito-sub-12345-abcdef")

        # Assert: All fields are present in result
        assert result is not None
        expected_fields = {
            "customer_id",
            "email",
            "full_name",
            "phone",
            "preferred_language",
            "cognito_sub",
            "email_verified",
            "created_at",
            "updated_at",
            "reservation_count",
        }
        assert set(result.keys()) == expected_fields

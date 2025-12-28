"""DynamoDB service wrapper for type-safe table operations."""

import os
from typing import Any, TypeVar

import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class DynamoDBService:
    """Service for DynamoDB operations with environment-aware table names."""

    def __init__(self, environment: str | None = None) -> None:
        """Initialize DynamoDB service.

        Args:
            environment: Environment name (dev/prod). Defaults to ENVIRONMENT env var.
        """
        self.environment = environment or os.getenv("ENVIRONMENT", "dev")
        self.name_prefix = f"summerhouse-{self.environment}"
        self._dynamodb = boto3.resource("dynamodb")
        self._client = boto3.client("dynamodb")

    def _table_name(self, table: str) -> str:
        """Get full table name with prefix."""
        return f"{self.name_prefix}-{table}"

    def _get_table(self, table: str) -> Any:
        """Get DynamoDB table resource."""
        return self._dynamodb.Table(self._table_name(table))

    # Generic CRUD operations

    def get_item(
        self,
        table: str,
        key: dict[str, Any],
    ) -> dict[str, Any] | None:
        """Get a single item by key.

        Args:
            table: Table name without prefix
            key: Primary key dict

        Returns:
            Item dict or None if not found
        """
        response = self._get_table(table).get_item(Key=key)
        item: dict[str, Any] | None = response.get("Item")
        return item

    def put_item(
        self,
        table: str,
        item: dict[str, Any],
        condition_expression: str | None = None,
    ) -> bool:
        """Put an item into the table.

        Args:
            table: Table name without prefix
            item: Item to store
            condition_expression: Optional condition for write

        Returns:
            True if successful, False if condition failed
        """
        try:
            kwargs: dict[str, Any] = {"Item": item}
            if condition_expression:
                kwargs["ConditionExpression"] = condition_expression

            self._get_table(table).put_item(**kwargs)
            return True
        except ClientError as e:
            if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
                return False
            raise

    def update_item(
        self,
        table: str,
        key: dict[str, Any],
        update_expression: str,
        expression_attribute_values: dict[str, Any],
        expression_attribute_names: dict[str, str] | None = None,
        condition_expression: str | None = None,
    ) -> dict[str, Any] | None:
        """Update an item with expressions.

        Args:
            table: Table name without prefix
            key: Primary key dict
            update_expression: DynamoDB update expression
            expression_attribute_values: Values for expression
            expression_attribute_names: Names for expression (for reserved words)
            condition_expression: Optional condition for update

        Returns:
            Updated attributes or None if condition failed
        """
        try:
            kwargs: dict[str, Any] = {
                "Key": key,
                "UpdateExpression": update_expression,
                "ExpressionAttributeValues": expression_attribute_values,
                "ReturnValues": "ALL_NEW",
            }
            if expression_attribute_names:
                kwargs["ExpressionAttributeNames"] = expression_attribute_names
            if condition_expression:
                kwargs["ConditionExpression"] = condition_expression

            response = self._get_table(table).update_item(**kwargs)
            attrs: dict[str, Any] | None = response.get("Attributes")
            return attrs
        except ClientError as e:
            if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
                return None
            raise

    def delete_item(
        self,
        table: str,
        key: dict[str, Any],
    ) -> bool:
        """Delete an item by key.

        Args:
            table: Table name without prefix
            key: Primary key dict

        Returns:
            True if deleted (or didn't exist)
        """
        self._get_table(table).delete_item(Key=key)
        return True

    def query(
        self,
        table: str,
        key_condition: Any,
        index_name: str | None = None,
        filter_expression: Any | None = None,
        limit: int | None = None,
        scan_index_forward: bool = True,
    ) -> list[dict[str, Any]]:
        """Query table or GSI.

        Args:
            table: Table name without prefix
            key_condition: Boto3 Key condition
            index_name: GSI name (optional)
            filter_expression: Additional filter (optional)
            limit: Max items to return
            scan_index_forward: Sort order (True=ascending)

        Returns:
            List of items
        """
        kwargs: dict[str, Any] = {
            "KeyConditionExpression": key_condition,
            "ScanIndexForward": scan_index_forward,
        }
        if index_name:
            kwargs["IndexName"] = index_name
        if filter_expression:
            kwargs["FilterExpression"] = filter_expression
        if limit:
            kwargs["Limit"] = limit

        response = self._get_table(table).query(**kwargs)
        items: list[dict[str, Any]] = response.get("Items", [])
        return items

    def batch_get(
        self,
        table: str,
        keys: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Batch get items by keys.

        Args:
            table: Table name without prefix
            keys: List of primary key dicts

        Returns:
            List of found items
        """
        if not keys:
            return []

        table_name = self._table_name(table)
        response = self._dynamodb.batch_get_item(
            RequestItems={table_name: {"Keys": keys}}
        )
        items: list[dict[str, Any]] = response.get("Responses", {}).get(table_name, [])
        return items

    def transact_write(
        self,
        items: list[dict[str, Any]],
    ) -> bool:
        """Execute transactional write for multiple items.

        Args:
            items: List of TransactWriteItem dicts

        Returns:
            True if successful, False if transaction failed
        """
        try:
            # Cast to satisfy boto3-stubs type checker
            self._client.transact_write_items(TransactItems=items)  # type: ignore[arg-type]
            return True
        except ClientError as e:
            if e.response["Error"]["Code"] == "TransactionCanceledException":
                return False
            raise

    # Convenience methods for common patterns

    def query_by_gsi(
        self,
        table: str,
        index_name: str,
        partition_key_name: str,
        partition_key_value: str,
        sort_key_condition: Any | None = None,
    ) -> list[dict[str, Any]]:
        """Query a GSI by partition key.

        Args:
            table: Table name without prefix
            index_name: GSI name
            partition_key_name: Name of partition key attribute
            partition_key_value: Value to query
            sort_key_condition: Optional sort key condition

        Returns:
            List of items
        """
        key_condition = Key(partition_key_name).eq(partition_key_value)
        if sort_key_condition:
            key_condition = key_condition & sort_key_condition

        return self.query(table, key_condition, index_name=index_name)

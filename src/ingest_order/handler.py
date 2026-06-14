import json
import os
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation

import boto3


ORDERS_TABLE_ENV_VAR = "ORDERS_TABLE_NAME"
HIGH_VALUE_THRESHOLD = Decimal("1000.00")


class ValidationError(Exception):
    """Raised when the incoming order payload is invalid."""


def lambda_handler(event, context):
    """Validate an incoming order request and store it in DynamoDB."""
    try:
        orders_table_name = os.environ[ORDERS_TABLE_ENV_VAR]
    except KeyError:
        return build_response(
            500,
            {
                "message": f"Missing required environment variable: {ORDERS_TABLE_ENV_VAR}"
            },
        )

    try:
        order = parse_order_payload(event)
        validated_order = validate_order(order)
    except ValidationError as error:
        return build_response(
            400,
            {
                "message": "Invalid order payload",
                "details": str(error),
            },
        )

    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")

    order_item = {
        "order_id": validated_order["order_id"],
        "customer_id": validated_order["customer_id"],
        "order_type": validated_order["order_type"],
        "items": convert_numbers_for_dynamodb(validated_order["items"]),
        "total_value": validated_order["total_value"],
        "status": "RECEIVED",
        "requires_high_value_review": validated_order["total_value"] >= HIGH_VALUE_THRESHOLD,
        "created_at": timestamp,
        "updated_at": timestamp,
    }

    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(orders_table_name)
    table.put_item(Item=order_item)

    return build_response(
        202,
        {
            "message": "Order received",
            "order_id": validated_order["order_id"],
            "status": "RECEIVED",
            "requires_high_value_review": order_item["requires_high_value_review"],
        },
    )


def parse_order_payload(event):
    """Extract and parse JSON from an API Gateway event body."""
    body = event.get("body", event)

    if isinstance(body, dict):
        return body

    if not isinstance(body, str) or not body.strip():
        raise ValidationError("Request body must contain a JSON object.")

    try:
        parsed_body = json.loads(body)
    except json.JSONDecodeError as error:
        raise ValidationError("Request body is not valid JSON.") from error

    if not isinstance(parsed_body, dict):
        raise ValidationError("Request body must be a JSON object.")

    return parsed_body


def validate_order(order):
    """Validate the required order fields and return a normalised order."""
    order_id = require_non_empty_string(order, "order_id")
    customer_id = require_non_empty_string(order, "customer_id")
    order_type = order.get("order_type", "standard")

    if not isinstance(order_type, str) or not order_type.strip():
        raise ValidationError("order_type must be a non-empty string when provided.")

    items = order.get("items")
    if not isinstance(items, list) or not items:
        raise ValidationError("items must be a non-empty list.")

    validated_items = [validate_order_item(item, index) for index, item in enumerate(items)]

    total_value = parse_positive_decimal(order.get("total_value"), "total_value")

    return {
        "order_id": order_id,
        "customer_id": customer_id,
        "order_type": order_type.strip(),
        "items": validated_items,
        "total_value": total_value,
    }


def validate_order_item(item, index):
    """Validate one order line item."""
    if not isinstance(item, dict):
        raise ValidationError(f"items[{index}] must be an object.")

    sku = item.get("sku")
    if not isinstance(sku, str) or not sku.strip():
        raise ValidationError(f"items[{index}].sku must be a non-empty string.")

    quantity = item.get("quantity")
    if not isinstance(quantity, int) or isinstance(quantity, bool) or quantity <= 0:
        raise ValidationError(f"items[{index}].quantity must be a positive integer.")

    unit_price = parse_positive_decimal(item.get("unit_price"), f"items[{index}].unit_price")

    return {
        "sku": sku.strip(),
        "quantity": quantity,
        "unit_price": unit_price,
    }


def require_non_empty_string(payload, field_name):
    """Return a trimmed string field or raise a validation error."""
    value = payload.get(field_name)

    if not isinstance(value, str) or not value.strip():
        raise ValidationError(f"{field_name} must be a non-empty string.")

    return value.strip()


def parse_positive_decimal(value, field_name):
    """Parse a positive numeric value into Decimal for DynamoDB compatibility."""
    if isinstance(value, bool):
        raise ValidationError(f"{field_name} must be a positive number.")

    try:
        decimal_value = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as error:
        raise ValidationError(f"{field_name} must be a positive number.") from error

    if decimal_value <= 0:
        raise ValidationError(f"{field_name} must be greater than zero.")

    return decimal_value


def convert_numbers_for_dynamodb(value):
    """Convert floats and nested numeric values into DynamoDB-safe Decimals."""
    if isinstance(value, bool):
        return value

    if isinstance(value, (int, float, Decimal)):
        return Decimal(str(value))

    if isinstance(value, list):
        return [convert_numbers_for_dynamodb(item) for item in value]

    if isinstance(value, dict):
        return {
            key: convert_numbers_for_dynamodb(item)
            for key, item in value.items()
        }

    return value


def build_response(status_code, body):
    """Build an API Gateway compatible JSON response."""
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": json.dumps(body),
    }

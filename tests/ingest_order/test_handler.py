import json
import os
import sys
import types
import unittest
from decimal import Decimal
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
HANDLER_PATH = REPO_ROOT / "src" / "ingest_order"

stored_items = []


class FakeTable:
    def put_item(self, Item):
        stored_items.append(Item)


class FakeDynamoDB:
    def Table(self, table_name):
        if table_name != "test-orders":
            raise AssertionError(f"Unexpected table name: {table_name}")

        return FakeTable()


sys.modules["boto3"] = types.SimpleNamespace(
    resource=lambda service_name: FakeDynamoDB()
)

sys.path.insert(0, str(HANDLER_PATH))

import handler


class IngestOrderHandlerTests(unittest.TestCase):
    def setUp(self):
        stored_items.clear()
        os.environ["ORDERS_TABLE_NAME"] = "test-orders"

    def tearDown(self):
        os.environ.pop("ORDERS_TABLE_NAME", None)

    def test_accepts_standard_order(self):
        response = handler.lambda_handler(
            {
                "body": json.dumps(
                    {
                        "order_id": "order-standard-001",
                        "customer_id": "customer-001",
                        "order_type": "standard",
                        "items": [
                            {
                                "sku": "SKU-001",
                                "quantity": 2,
                                "unit_price": 19.99
                            }
                        ],
                        "total_value": 39.98
                    }
                )
            },
            None,
        )

        body = json.loads(response["body"])

        self.assertEqual(response["statusCode"], 202)
        self.assertEqual(body["status"], "RECEIVED")
        self.assertFalse(body["requires_high_value_review"])
        self.assertEqual(len(stored_items), 1)
        self.assertEqual(stored_items[0]["status"], "RECEIVED")
        self.assertIsInstance(stored_items[0]["total_value"], Decimal)
        self.assertIsInstance(stored_items[0]["items"][0]["unit_price"], Decimal)

    def test_flags_high_value_order(self):
        response = handler.lambda_handler(
            {
                "body": json.dumps(
                    {
                        "order_id": "order-high-value-001",
                        "customer_id": "customer-002",
                        "order_type": "standard",
                        "items": [
                            {
                                "sku": "SKU-999",
                                "quantity": 1,
                                "unit_price": 1500.00
                            }
                        ],
                        "total_value": 1500.00
                    }
                )
            },
            None,
        )

        body = json.loads(response["body"])

        self.assertEqual(response["statusCode"], 202)
        self.assertTrue(body["requires_high_value_review"])
        self.assertTrue(stored_items[0]["requires_high_value_review"])

    def test_rejects_invalid_payload(self):
        response = handler.lambda_handler(
            {
                "body": json.dumps(
                    {
                        "customer_id": "customer-003",
                        "items": [],
                        "total_value": -10
                    }
                )
            },
            None,
        )

        body = json.loads(response["body"])

        self.assertEqual(response["statusCode"], 400)
        self.assertEqual(body["message"], "Invalid order payload")
        self.assertEqual(len(stored_items), 0)

    def test_rejects_mismatched_total(self):
        response = handler.lambda_handler(
            {
                "body": json.dumps(
                    {
                        "order_id": "order-bad-total-001",
                        "customer_id": "customer-004",
                        "order_type": "standard",
                        "items": [
                            {
                                "sku": "SKU-001",
                                "quantity": 1,
                                "unit_price": 10.00
                            }
                        ],
                        "total_value": 9999.00
                    }
                )
            },
            None,
        )

        body = json.loads(response["body"])

        self.assertEqual(response["statusCode"], 400)
        self.assertIn("total_value must match item total", body["details"])
        self.assertEqual(len(stored_items), 0)

    def test_missing_table_environment_variable_returns_500(self):
        os.environ.pop("ORDERS_TABLE_NAME", None)

        response = handler.lambda_handler(
            {
                "body": json.dumps(
                    {
                        "order_id": "order-standard-001",
                        "customer_id": "customer-001",
                        "order_type": "standard",
                        "items": [
                            {
                                "sku": "SKU-001",
                                "quantity": 2,
                                "unit_price": 19.99
                            }
                        ],
                        "total_value": 39.98
                    }
                )
            },
            None,
        )

        body = json.loads(response["body"])

        self.assertEqual(response["statusCode"], 500)
        self.assertIn("Missing required environment variable", body["message"])
        self.assertEqual(len(stored_items), 0)


if __name__ == "__main__":
    unittest.main()

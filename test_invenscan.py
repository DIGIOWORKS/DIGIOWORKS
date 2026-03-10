"""
Test suite for InvenScan.
Validates database, utils, and web search components without requiring a display.
"""

import os
import sys
import tempfile
import csv
import unittest


class TestDatabase(unittest.TestCase):
    """Tests for the InventoryDatabase module."""

    def setUp(self):
        self.db_path = os.path.join(tempfile.gettempdir(), "test_invenscan.db")
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        from database import InventoryDatabase
        self.db = InventoryDatabase(self.db_path)

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_add_and_retrieve_item(self):
        item_id = self.db.add_item("Test Widget", 19.99, 5, "New", "A test item", "Test", "", "")
        self.assertGreater(item_id, 0)
        item = self.db.get_item(item_id)
        self.assertIsNotNone(item)
        self.assertEqual(item["title"], "Test Widget")
        self.assertAlmostEqual(item["price"], 19.99)
        self.assertEqual(item["quantity"], 5)
        self.assertEqual(item["status"], "active")

    def test_update_item(self):
        item_id = self.db.add_item("Old Title", 9.99, 1)
        updated = self.db.update_item(item_id, "New Title", 29.99, 3)
        self.assertTrue(updated)
        item = self.db.get_item(item_id)
        self.assertEqual(item["title"], "New Title")
        self.assertAlmostEqual(item["price"], 29.99)

    def test_delete_item(self):
        item_id = self.db.add_item("Delete Me", 1.00, 1)
        deleted = self.db.delete_item(item_id)
        self.assertTrue(deleted)
        self.assertIsNone(self.db.get_item(item_id))

    def test_search_items(self):
        self.db.add_item("iPhone 13 Pro", 799.99, 1)
        self.db.add_item("Samsung Galaxy", 699.99, 2)
        results = self.db.search_items("iPhone")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["title"], "iPhone 13 Pro")

    def test_search_by_barcode(self):
        self.db.add_item("Barcode Item", 5.00, 10, barcode="012345678901")
        item = self.db.get_item_by_barcode("012345678901")
        self.assertIsNotNone(item)
        self.assertEqual(item["title"], "Barcode Item")

    def test_get_items_by_status(self):
        self.db.add_item("Active Item", 10.00, 1, status="active")
        self.db.add_item("Sold Item", 20.00, 1, status="sold")
        active = self.db.get_items_by_status("active")
        sold = self.db.get_items_by_status("sold")
        self.assertTrue(any(i["title"] == "Active Item" for i in active))
        self.assertTrue(any(i["title"] == "Sold Item" for i in sold))

    def test_listing_counter(self):
        num1 = self.db.get_next_listing_number()
        num2 = self.db.get_next_listing_number()
        self.assertEqual(num2, num1 + 1)

    def test_get_all_items(self):
        for i in range(3):
            self.db.add_item(f"Item {i}", float(i), 1)
        items = self.db.get_all_items()
        self.assertEqual(len(items), 3)


class TestUtils(unittest.TestCase):
    """Tests for utility functions."""

    def test_validate_valid_data(self):
        from utils import validate_item_data
        valid, msg = validate_item_data("Test Item", "29.99", "5")
        self.assertTrue(valid)
        self.assertEqual(msg, "")

    def test_validate_empty_title(self):
        from utils import validate_item_data
        valid, msg = validate_item_data("", "29.99", "5")
        self.assertFalse(valid)
        self.assertIn("Title", msg)

    def test_validate_invalid_price(self):
        from utils import validate_item_data
        valid, msg = validate_item_data("Item", "not_a_price", "5")
        self.assertFalse(valid)
        self.assertIn("Price", msg)

    def test_validate_negative_price(self):
        from utils import validate_item_data
        valid, msg = validate_item_data("Item", "-1.00", "5")
        self.assertFalse(valid)

    def test_validate_invalid_quantity(self):
        from utils import validate_item_data
        valid, msg = validate_item_data("Item", "10.00", "abc")
        self.assertFalse(valid)
        self.assertIn("Quantity", msg)

    def test_export_to_csv(self):
        from utils import export_to_csv
        items = [
            {
                "title": "test widget",
                "price": 9.99,
                "quantity": 3,
                "condition": "New",
                "description": "A widget",
                "category": "Test",
                "barcode": "123456",
                "image_path": "",
            }
        ]
        out_path = os.path.join(tempfile.gettempdir(), "test_export.csv")
        result = export_to_csv(items, out_path)
        self.assertTrue(os.path.exists(result))

        with open(result, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            row = next(reader)
            # Title must be upper-cased
            self.assertEqual(row["Title"], "TEST WIDGET")
            self.assertEqual(row["Barcode"], "123456")

        os.remove(result)

    def test_format_price(self):
        from utils import format_price
        self.assertEqual(format_price(9.99), "$9.99")
        self.assertEqual(format_price(0), "$0.00")

    def test_truncate_text(self):
        from utils import truncate_text
        short = "Hello"
        self.assertEqual(truncate_text(short, 10), short)
        long_text = "A" * 60
        result = truncate_text(long_text, 50)
        self.assertEqual(len(result), 50)
        self.assertTrue(result.endswith("..."))


class TestWebSearch(unittest.TestCase):
    """Tests for the WebSearcher module."""

    def setUp(self):
        from web_search import WebSearcher
        self.searcher = WebSearcher()

    def test_generate_suggestions(self):
        suggestions = self.searcher.generate_search_suggestions("laptop")
        self.assertGreater(len(suggestions), 0)
        self.assertTrue(any("laptop" in s.lower() for s in suggestions))

    def test_empty_query_returns_no_suggestions(self):
        suggestions = self.searcher.generate_search_suggestions("")
        self.assertEqual(suggestions, [])

    def test_simulate_terapeak_search(self):
        results = self.searcher.simulate_terapeak_search("smartphone")
        self.assertGreater(len(results), 0)
        first = results[0]
        self.assertIn("condition", first)
        self.assertIn("avg_price", first)

    def test_price_recommendation(self):
        rec = self.searcher.get_price_recommendation("gaming laptop", "Used - Good")
        self.assertIn("recommended_price", rec)
        self.assertGreater(rec["recommended_price"], 0)

    def test_search_history(self):
        self.searcher.simulate_terapeak_search("watch")
        self.searcher.simulate_terapeak_search("ring")
        history = self.searcher.get_search_history()
        self.assertIn("watch", history)
        self.assertIn("ring", history)


class TestEbayAPI(unittest.TestCase):
    """Tests for the eBayAPIClient module (no live network calls)."""

    def setUp(self):
        from ebay_api import eBayAPIClient
        self.client = eBayAPIClient()

    def test_not_configured_by_default(self):
        # Without a real ebay_config.json the client should report unconfigured
        # (in the test environment there should be no config file)
        if not os.path.exists("ebay_config.json"):
            self.assertFalse(self.client.is_configured())

    def test_simulated_terapeak_data(self):
        data = self.client.get_simulated_terapeak_data("headphones")
        self.assertGreater(len(data), 0)
        first = data[0]
        self.assertIn("condition", first)
        self.assertIn("avg_sold_price", first)
        self.assertIn("source", first)
        self.assertEqual(first["source"], "Terapeak Simulation")

    def test_standalone_function(self):
        from ebay_api import get_simulated_terapeak_data
        data = get_simulated_terapeak_data("shoes")
        self.assertGreater(len(data), 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)

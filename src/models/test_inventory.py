"""Tests for inventory.add_stock, edit_product, delete_product, and list_products."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import inventory


class InventoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmpdir.cleanup)
        self._orig_data_file = inventory.DATA_FILE
        inventory.DATA_FILE = Path(self._tmpdir.name) / "test_inventory.json"
        self.addCleanup(self._restore_data_file)

    def _restore_data_file(self) -> None:
        inventory.DATA_FILE = self._orig_data_file

    def test_add_stock_creates_product(self) -> None:
        inventory.add_stock("Mug", 3)
        self.assertEqual(inventory.list_products(), [("Mug", 3)])

    def test_add_stock_increments_existing(self) -> None:
        inventory.add_stock("Pen", 10)
        inventory.add_stock("Pen", 5)
        self.assertEqual(inventory.list_products(), [("Pen", 15)])

    def test_add_stock_strips_name(self) -> None:
        inventory.add_stock("  Eraser  ", 2)
        self.assertEqual(inventory.list_products(), [("Eraser", 2)])

    def test_add_stock_empty_name_raises(self) -> None:
        with self.assertRaisesRegex(ValueError, "empty"):
            inventory.add_stock("   ", 1)
        with self.assertRaisesRegex(ValueError, "empty"):
            inventory.add_stock("", 1)

    def test_add_stock_non_positive_quantity_raises(self) -> None:
        inventory.add_stock("X", 1)
        with self.assertRaisesRegex(ValueError, "positive"):
            inventory.add_stock("X", 0)
        with self.assertRaisesRegex(ValueError, "positive"):
            inventory.add_stock("Y", -5)

    def test_list_products_empty(self) -> None:
        self.assertEqual(inventory.list_products(), [])

    def test_list_products_sorted_case_insensitive(self) -> None:
        inventory.add_stock("apple", 1)
        inventory.add_stock("Banana", 2)
        inventory.add_stock("apricot", 3)
        names = [n for n, _ in inventory.list_products()]
        self.assertEqual(names, ["apple", "apricot", "Banana"])

    def test_edit_product_rename_only(self) -> None:
        inventory.add_stock("Old", 7)
        inventory.edit_product("Old", new_name="New")
        self.assertEqual(inventory.list_products(), [("New", 7)])

    def test_edit_product_add_and_remove_stock(self) -> None:
        inventory.add_stock("Item", 10)
        inventory.edit_product("Item", add_quantity=4, remove_quantity=3)
        self.assertEqual(inventory.list_products(), [("Item", 11)])

    def test_edit_product_rename_and_quantities(self) -> None:
        inventory.add_stock("A", 5)
        inventory.edit_product("A", new_name="B", add_quantity=2, remove_quantity=1)
        self.assertEqual(inventory.list_products(), [("B", 6)])

    def test_edit_product_keep_name_when_new_name_none(self) -> None:
        inventory.add_stock("Same", 3)
        inventory.edit_product("Same", new_name=None, add_quantity=1)
        self.assertEqual(inventory.list_products(), [("Same", 4)])

    def test_edit_product_missing_raises(self) -> None:
        with self.assertRaises(KeyError):
            inventory.edit_product("Nope", add_quantity=1)

    def test_edit_product_negative_result_raises(self) -> None:
        inventory.add_stock("Low", 2)
        with self.assertRaisesRegex(ValueError, "negative"):
            inventory.edit_product("Low", remove_quantity=5)

    def test_edit_product_duplicate_new_name_raises(self) -> None:
        inventory.add_stock("First", 1)
        inventory.add_stock("Second", 2)
        with self.assertRaisesRegex(ValueError, "already exists"):
            inventory.edit_product("First", new_name="Second")

    def test_edit_product_empty_new_name_raises(self) -> None:
        inventory.add_stock("X", 1)
        with self.assertRaisesRegex(ValueError, "empty"):
            inventory.edit_product("X", new_name="   ")

    def test_edit_product_negative_adjustments_raise(self) -> None:
        inventory.add_stock("Z", 5)
        with self.assertRaisesRegex(ValueError, "non-negative"):
            inventory.edit_product("Z", add_quantity=-1)
        with self.assertRaisesRegex(ValueError, "non-negative"):
            inventory.edit_product("Z", remove_quantity=-1)

    def test_delete_product_removes(self) -> None:
        inventory.add_stock("Gone", 1)
        inventory.delete_product("Gone")
        self.assertEqual(inventory.list_products(), [])

    def test_delete_product_strips_name(self) -> None:
        inventory.add_stock("Trim", 1)
        inventory.delete_product("  Trim  ")
        self.assertEqual(inventory.list_products(), [])

    def test_delete_product_missing_raises(self) -> None:
        with self.assertRaises(KeyError):
            inventory.delete_product("Missing")

    def test_delete_product_empty_name_raises(self) -> None:
        with self.assertRaisesRegex(ValueError, "empty"):
            inventory.delete_product("  ")

    def test_load_ignores_invalid_json_file(self) -> None:
        inventory.DATA_FILE.write_text("{not json", encoding="utf-8")
        self.assertEqual(inventory.list_products(), [])
        inventory.add_stock("AfterBadFile", 1)
        self.assertEqual(inventory.list_products(), [("AfterBadFile", 1)])

    def test_persist_round_trip(self) -> None:
        inventory.add_stock("Persist", 9)
        raw = json.loads(inventory.DATA_FILE.read_text(encoding="utf-8"))
        self.assertEqual(raw.get("Persist"), 9)


if __name__ == "__main__":
    unittest.main()

"""Tests for inventory create_product, add_stock, edit_product, delete_product, list_products."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_SRC_DIR = _PROJECT_ROOT / "src"
if _SRC_DIR.is_dir() and str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

from App.services import inventory


class TestInventory(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmpdir.cleanup)
        self._orig_data_file = inventory.DATA_FILE
        inventory.DATA_FILE = Path(self._tmpdir.name) / "test_inventory.json"
        self.addCleanup(self._restore_data_file)

    def _restore_data_file(self) -> None:
        inventory.DATA_FILE = self._orig_data_file

    # --- create_product ---

    def test_create_product_new(self) -> None:
        inventory.create_product("Mug", 3, 0.0)
        self.assertEqual(inventory.list_products(), [("Mug", 3, 0.0)])

    def test_create_product_with_price(self) -> None:
        inventory.create_product("Kettle", 2, 24.99)
        self.assertEqual(inventory.list_products(), [("Kettle", 2, 24.99)])

    def test_create_product_strips_name(self) -> None:
        inventory.create_product("  Eraser  ", 2, 0.0)
        self.assertEqual(inventory.list_products(), [("Eraser", 2, 0.0)])

    def test_create_product_empty_name_raises(self) -> None:
        with self.assertRaisesRegex(ValueError, "empty"):
            inventory.create_product("   ", 1, 0.0)
        with self.assertRaisesRegex(ValueError, "empty"):
            inventory.create_product("", 1, 0.0)

    def test_create_product_non_positive_quantity_raises(self) -> None:
        with self.assertRaisesRegex(ValueError, "positive"):
            inventory.create_product("A", 0, 0.0)
        with self.assertRaisesRegex(ValueError, "positive"):
            inventory.create_product("B", -3, 0.0)

    def test_create_product_negative_price_raises(self) -> None:
        with self.assertRaisesRegex(ValueError, "Price"):
            inventory.create_product("C", 1, -0.01)

    def test_create_product_duplicate_raises(self) -> None:
        inventory.create_product("Dup", 1, 5.0)
        with self.assertRaisesRegex(ValueError, "already exists"):
            inventory.create_product("Dup", 2, 0.0)

    # --- add_stock (existing products only) ---

    def test_add_stock_increments_existing(self) -> None:
        inventory.create_product("Pen", 10, 0.0)
        inventory.add_stock("Pen", 5)
        self.assertEqual(inventory.list_products(), [("Pen", 15, 0.0)])

    def test_add_stock_missing_product_raises(self) -> None:
        with self.assertRaisesRegex(KeyError, "not found"):
            inventory.add_stock("Nope", 1)

    def test_add_stock_non_positive_quantity_raises(self) -> None:
        inventory.create_product("X", 1, 0.0)
        with self.assertRaisesRegex(ValueError, "positive"):
            inventory.add_stock("X", 0)
        with self.assertRaisesRegex(ValueError, "positive"):
            inventory.add_stock("X", -5)

    # --- list_products ---

    def test_list_products_empty(self) -> None:
        self.assertEqual(inventory.list_products(), [])

    def test_list_products_sorted_case_insensitive(self) -> None:
        inventory.create_product("apple", 1, 0.0)
        inventory.create_product("Banana", 2, 0.0)
        inventory.create_product("apricot", 3, 0.0)
        names = [n for n, _, _ in inventory.list_products()]
        self.assertEqual(names, ["apple", "apricot", "Banana"])

    # --- edit_product ---

    def test_edit_product_rename_only(self) -> None:
        inventory.create_product("Old", 7, 0.0)
        inventory.edit_product("Old", new_name="New")
        self.assertEqual(inventory.list_products(), [("New", 7, 0.0)])

    def test_edit_product_add_and_remove_stock(self) -> None:
        inventory.create_product("Item", 10, 0.0)
        inventory.edit_product("Item", add_quantity=4, remove_quantity=3)
        self.assertEqual(inventory.list_products(), [("Item", 11, 0.0)])

    def test_edit_product_rename_and_quantities(self) -> None:
        inventory.create_product("A", 5, 0.0)
        inventory.edit_product("A", new_name="B", add_quantity=2, remove_quantity=1)
        self.assertEqual(inventory.list_products(), [("B", 6, 0.0)])

    def test_edit_product_sets_price(self) -> None:
        inventory.create_product("Book", 2, 0.0)
        inventory.edit_product("Book", price=12.5)
        self.assertEqual(inventory.list_products(), [("Book", 2, 12.5)])

    def test_edit_product_price_preserved_on_rename(self) -> None:
        inventory.create_product("X", 1, 9.0)
        inventory.edit_product("X", new_name="Y")
        self.assertEqual(inventory.list_products(), [("Y", 1, 9.0)])

    def test_edit_product_negative_price_raises(self) -> None:
        inventory.create_product("P", 1, 0.0)
        with self.assertRaisesRegex(ValueError, "Price"):
            inventory.edit_product("P", price=-1.0)

    def test_edit_product_keep_name_when_new_name_none(self) -> None:
        inventory.create_product("Same", 3, 0.0)
        inventory.edit_product("Same", new_name=None, add_quantity=1)
        self.assertEqual(inventory.list_products(), [("Same", 4, 0.0)])

    def test_edit_product_missing_raises(self) -> None:
        with self.assertRaises(KeyError):
            inventory.edit_product("Nope", add_quantity=1)

    def test_edit_product_negative_result_raises(self) -> None:
        inventory.create_product("Low", 2, 0.0)
        with self.assertRaisesRegex(ValueError, "negative"):
            inventory.edit_product("Low", remove_quantity=5)

    def test_edit_product_duplicate_new_name_raises(self) -> None:
        inventory.create_product("First", 1, 0.0)
        inventory.create_product("Second", 2, 0.0)
        with self.assertRaisesRegex(ValueError, "already exists"):
            inventory.edit_product("First", new_name="Second")

    def test_edit_product_empty_new_name_raises(self) -> None:
        inventory.create_product("X", 1, 0.0)
        with self.assertRaisesRegex(ValueError, "empty"):
            inventory.edit_product("X", new_name="   ")

    def test_edit_product_negative_adjustments_raise(self) -> None:
        inventory.create_product("Z", 5, 0.0)
        with self.assertRaisesRegex(ValueError, "non-negative"):
            inventory.edit_product("Z", add_quantity=-1)
        with self.assertRaisesRegex(ValueError, "non-negative"):
            inventory.edit_product("Z", remove_quantity=-1)

    # --- delete_product ---

    def test_delete_product_removes(self) -> None:
        inventory.create_product("Gone", 1, 0.0)
        inventory.delete_product("Gone")
        self.assertEqual(inventory.list_products(), [])

    def test_delete_product_strips_name(self) -> None:
        inventory.create_product("Trim", 1, 0.0)
        inventory.delete_product("  Trim  ")
        self.assertEqual(inventory.list_products(), [])

    def test_delete_product_missing_raises(self) -> None:
        with self.assertRaises(KeyError):
            inventory.delete_product("Missing")

    def test_delete_product_empty_name_raises(self) -> None:
        with self.assertRaisesRegex(ValueError, "empty"):
            inventory.delete_product("  ")

    # --- persistence / load ---

    def test_load_ignores_invalid_json_file(self) -> None:
        inventory.DATA_FILE.write_text("{not json", encoding="utf-8")
        self.assertEqual(inventory.list_products(), [])
        inventory.create_product("AfterBadFile", 1, 0.0)
        self.assertEqual(inventory.list_products(), [("AfterBadFile", 1, 0.0)])

    def test_persist_round_trip(self) -> None:
        inventory.create_product("Persist", 9, 3.5)
        raw = json.loads(inventory.DATA_FILE.read_text(encoding="utf-8"))
        self.assertEqual(raw.get("Persist"), {"quantity": 9, "price": 3.5})

    def test_load_legacy_int_quantity(self) -> None:
        inventory.DATA_FILE.write_text(
            json.dumps({"Legacy": 4}),
            encoding="utf-8",
        )
        self.assertEqual(inventory.list_products(), [("Legacy", 4, 0.0)])


if __name__ == "__main__":
    unittest.main()

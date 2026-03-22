"""Tests for sales.register_sale, list_sales, revenue helpers, and clear_sales_history."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_SRC_DIR = _PROJECT_ROOT / "src"
if _SRC_DIR.is_dir() and str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

from App.services import inventory, sales


class TestSales(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmpdir.cleanup)

        self._orig_inventory_file = inventory.DATA_FILE
        self._orig_sales_file = sales.SALES_FILE
        inventory.DATA_FILE = Path(self._tmpdir.name) / "inventory_data.json"
        sales.SALES_FILE = Path(self._tmpdir.name) / "sales_data.json"
        self.addCleanup(self._restore_paths)

        inventory._save({})
        sales._save_sales([])

    def _restore_paths(self) -> None:
        inventory.DATA_FILE = self._orig_inventory_file
        sales.SALES_FILE = self._orig_sales_file

    def test_register_sale_successfully(self) -> None:
        inventory.create_product("Soap", 10, 250.0)

        sale = sales.register_sale("Soap", 2)

        self.assertEqual(sale["product"], "Soap")
        self.assertEqual(sale["quantity"], 2)
        self.assertEqual(sale["unit_price"], 250.0)
        self.assertEqual(sale["total"], 500.0)

        products = inventory._load()
        self.assertEqual(products["Soap"]["quantity"], 8)

    def test_register_sale_with_nonexistent_product(self) -> None:
        with self.assertRaises(ValueError) as context:
            sales.register_sale("Shampoo", 1)

        self.assertEqual(str(context.exception), "Product does not exist.")

    def test_register_sale_with_insufficient_stock(self) -> None:
        inventory.create_product("Soap", 3, 250.0)

        with self.assertRaises(ValueError) as context:
            sales.register_sale("Soap", 5)

        self.assertEqual(str(context.exception), "Insufficient stock.")

    def test_register_sale_with_invalid_quantity(self) -> None:
        inventory.create_product("Soap", 10, 250.0)

        with self.assertRaises(ValueError) as context:
            sales.register_sale("Soap", 0)

        self.assertEqual(str(context.exception), "Quantity sold must be positive.")

    def test_list_sales(self) -> None:
        inventory.create_product("Soap", 10, 250.0)
        sales.register_sale("Soap", 2)
        sales.register_sale("Soap", 1)

        all_sales = sales.list_sales()

        self.assertEqual(len(all_sales), 2)

    def test_get_total_revenue(self) -> None:
        inventory.create_product("Soap", 10, 250.0)
        inventory.create_product("Detergent", 5, 1000.0)

        sales.register_sale("Soap", 2)
        sales.register_sale("Detergent", 1)

        self.assertEqual(sales.get_total_revenue(), 1500.0)

    def test_get_sales_by_product(self) -> None:
        inventory.create_product("Soap", 10, 250.0)
        inventory.create_product("Detergent", 5, 1000.0)

        sales.register_sale("Soap", 2)
        sales.register_sale("Soap", 1)
        sales.register_sale("Detergent", 1)

        soap_sales = sales.get_sales_by_product("Soap")

        self.assertEqual(len(soap_sales), 2)
        self.assertTrue(all(s["product"] == "Soap" for s in soap_sales))

    def test_get_total_units_sold(self) -> None:
        inventory.create_product("Soap", 10, 250.0)

        sales.register_sale("Soap", 2)
        sales.register_sale("Soap", 3)

        self.assertEqual(sales.get_total_units_sold("Soap"), 5)

    def test_clear_sales_history(self) -> None:
        inventory.create_product("Soap", 10, 250.0)
        sales.register_sale("Soap", 2)

        sales.clear_sales_history()

        self.assertEqual(sales.list_sales(), [])


if __name__ == "__main__":
    unittest.main()

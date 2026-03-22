import json
from datetime import datetime
from pathlib import Path
from typing import Any

from App.services import inventory

SALES_FILE = Path(__file__).resolve().with_name("sales_data.json")


def _load_sales() -> list[dict[str, Any]]:
    if not SALES_FILE.exists():
        return []

    try:
        with open(SALES_FILE, encoding="utf-8") as file:
            data = json.load(file)
            return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def _save_sales(records: list[dict[str, Any]]) -> None:
    with open(SALES_FILE, "w", encoding="utf-8") as file:
        json.dump(records, file, indent=4, ensure_ascii=False)


def register_sale(product_name: str, quantity: int) -> dict[str, Any]:
    """
    Register a sale, decrease stock, and save the sale record.
    """
    product_name = product_name.strip()

    if not product_name:
        raise ValueError("Product name cannot be empty.")
    if quantity <= 0:
        raise ValueError("Quantity sold must be positive.")

    products = inventory._load()

    if product_name not in products:
        raise ValueError("Product does not exist.")

    product = products[product_name]
    available_stock = product["quantity"]
    unit_price = float(product["price"])

    if quantity > available_stock:
        raise ValueError("Insufficient stock.")

    products[product_name]["quantity"] -= quantity
    inventory._save(products)

    sale: dict[str, Any] = {
        "product": product_name,
        "quantity": quantity,
        "unit_price": unit_price,
        "total": round(quantity * unit_price, 2),
        "date": datetime.now().isoformat(timespec="seconds"),
    }

    records = _load_sales()
    records.append(sale)
    _save_sales(records)

    return sale


def list_sales() -> list[dict[str, Any]]:
    """
    Return all sales ordered from newest to oldest.
    """
    records = _load_sales()
    return sorted(records, key=lambda s: s["date"], reverse=True)


def get_total_revenue() -> float:
    """
    Return the total revenue generated from all sales.
    """
    records = _load_sales()
    return round(sum(s["total"] for s in records), 2)


def get_sales_by_product(product_name: str) -> list[dict[str, Any]]:
    """
    Return all sales for a given product.
    """
    product_name = product_name.strip()

    if not product_name:
        raise ValueError("Product name cannot be empty.")

    records = _load_sales()
    return [s for s in records if s["product"] == product_name]


def get_total_units_sold(product_name: str) -> int:
    """
    Return the total number of units sold for a product.
    """
    product_name = product_name.strip()

    if not product_name:
        raise ValueError("Product name cannot be empty.")

    records = get_sales_by_product(product_name)
    return sum(s["quantity"] for s in records)


def clear_sales_history() -> None:
    """
    Delete all sales history.
    """
    _save_sales([])

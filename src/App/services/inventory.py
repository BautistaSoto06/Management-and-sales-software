"""
Simple inventory manager: add stock, edit products, delete products, list products.
Data is stored in inventory_data.json next to this file.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, TypedDict


class _ProductRow(TypedDict):
    quantity: int
    price: float


DATA_FILE = Path(__file__).resolve().with_name("inventory_data.json")


def _normalize_value(v: Any) -> _ProductRow | None:
    """Accept legacy int (quantity only) or dict with quantity and optional price."""
    if isinstance(v, int) and v >= 0:
        return {"quantity": v, "price": 0.0}
    if isinstance(v, dict):
        q = v.get("quantity")
        if not isinstance(q, int) or q < 0:
            return None
        raw_p = v.get("price", 0.0)
        if isinstance(raw_p, bool) or not isinstance(raw_p, (int, float)):
            return None
        p = float(raw_p)
        if p < 0:
            return None
        return {"quantity": q, "price": p}
    return None


def _load() -> dict[str, _ProductRow]:
    if not DATA_FILE.exists():
        return {}
    try:
        raw = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    if not isinstance(raw, dict):
        return {}
    out: dict[str, _ProductRow] = {}
    for k, v in raw.items():
        if not isinstance(k, str):
            continue
        name = k.strip()
        row = _normalize_value(v)
        if row is not None:
            out[name] = row
    return out


def _save(data: dict[str, _ProductRow]) -> None:
    serializable = {name: dict(row) for name, row in sorted(data.items())}
    DATA_FILE.write_text(
        json.dumps(serializable, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def create_product(name: str, quantity: int, price: float) -> None:
    """Add quantity to a product. Creates the product if it does not exist."""
    name = name.strip()
    price = float(price)
    if price < 0:
        raise ValueError("Price cannot be negative.")
    if not name:
        raise ValueError("Product name cannot be empty.")
    if quantity <= 0:
        raise ValueError("Quantity to add must be positive.")

    data = _load()
    if name in data:
        raise ValueError(f"Product {name!r} already exists.")

    data[name] = {"quantity": quantity, "price": price}
    _save(data)

def add_stock(name: str, quantity: int) -> None:
    if quantity <= 0:
        raise ValueError("Quantity to add must be positive.")
    data = _load()
    if name not in data:
        raise KeyError(f"Product not found: {name!r}")
    data[name]["quantity"] += quantity
    _save(data)

def edit_product(
    current_name: str,
    *,
    new_name: str | None = None,
    add_quantity: int = 0,
    remove_quantity: int = 0,
    price: float | None = None,
) -> None:
    """
    Edit a product: optional rename, optional add/remove stock, optional new price.
    Pass ``price`` to set unit price; omit or pass None to leave it unchanged.
    """
    current_name = current_name.strip()
    if not current_name:
        raise ValueError("Current product name cannot be empty.")

    data = _load()
    if current_name not in data:
        raise KeyError(f"Product not found: {current_name!r}")

    final_name = (new_name.strip() if new_name is not None else current_name)
    if not final_name:
        raise ValueError("New name cannot be empty.")

    if add_quantity < 0 or remove_quantity < 0:
        raise ValueError("add_quantity and remove_quantity must be non-negative.")

    row = data.pop(current_name)
    qty = row["quantity"] + add_quantity - remove_quantity
    if qty < 0:
        raise ValueError("Stock cannot be negative after this change.")

    if final_name != current_name and final_name in data:
        raise ValueError(f"A product named {final_name!r} already exists.")

    new_price = row["price"]
    if price is not None:
        if isinstance(price, bool) or not isinstance(price, (int, float)):
            raise TypeError("price must be a number.")
        new_price = float(price)
        if new_price < 0:
            raise ValueError("Price cannot be negative.")

    data[final_name] = {"quantity": qty, "price": new_price}
    _save(data)


def delete_product(name: str) -> None:
    """Remove a product entirely."""
    name = name.strip()
    if not name:
        raise ValueError("Product name cannot be empty.")

    data = _load()
    if name not in data:
        raise KeyError(f"Product not found: {name!r}")
    del data[name]
    _save(data)


def list_products() -> list[tuple[str, int, float]]:
    """Return all products as (name, quantity, price), sorted by name."""
    data = _load()
    return sorted(
        ((n, r["quantity"], r["price"]) for n, r in data.items()),
        key=lambda x: x[0].lower(),
    )


def _prompt_int(message: str) -> int:
    s = input(message).strip()
    try:
        return int(s)
    except ValueError as e:
        raise ValueError("Please enter a whole number.") from e


def _menu() -> None:
    while True:
        print("\n--- Inventory ---")
        print("1. Add stock")
        print("2. Edit product")
        print("3. Delete product")
        print("4. List products")
        print("5. Exit")
        choice = input("Choose (1-5): ").strip()

        if choice == "1":
            name = input("Product name: ").strip()
            try:
                qty = _prompt_int("Initial quantity: ")
                price_s = input("Unit price: ").strip() or "0"
                unit_price = float(price_s)
                create_product(name, qty, unit_price)
                print("Product created.")
            except (ValueError, KeyError) as e:
                print(f"Error: {e}")

        elif choice == "2":
            current = input("Current product name: ").strip()
            print("Leave blank to keep current name / price.")
            new_name = input("New name (optional): ").strip() or None
            add_s = input("Quantity to add (0 if none): ").strip() or "0"
            rem_s = input("Quantity to remove (0 if none): ").strip() or "0"
            price_in = input("New unit price (blank to keep): ").strip()
            try:
                add_q = int(add_s)
                rem_q = int(rem_s)
                new_price = float(price_in) if price_in else None
                edit_product(
                    current,
                    new_name=new_name,
                    add_quantity=add_q,
                    remove_quantity=rem_q,
                    price=new_price,
                )
                print("Product updated.")
            except (ValueError, KeyError, TypeError) as e:
                print(f"Error: {e}")

        elif choice == "3":
            name = input("Product name to delete: ").strip()
            try:
                delete_product(name)
                print("Product deleted.")
            except (ValueError, KeyError) as e:
                print(f"Error: {e}")

        elif choice == "4":
            items = list_products()
            if not items:
                print("No products.")
            else:
                for n, q, p in items:
                    print(f"  {n}: qty={q}, price={p}")

        elif choice == "5":
            print("Goodbye.")
            break
        else:
            print("Invalid choice.")


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    if argv:
        print("This script runs interactively. Run without arguments.", file=sys.stderr)
        return 1
    _menu()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

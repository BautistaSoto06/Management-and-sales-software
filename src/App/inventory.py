"""
Simple inventory manager: add stock, edit products, delete products, list products.
Data is stored in inventory_data.json next to this file.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

DATA_FILE = Path(__file__).resolve().with_name("inventory_data.json")


def _load() -> dict[str, int]:
    if not DATA_FILE.exists():
        return {}
    try:
        raw = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    if not isinstance(raw, dict):
        return {}
    out: dict[str, int] = {}
    for k, v in raw.items():
        if isinstance(k, str) and isinstance(v, int) and v >= 0:
            out[k.strip()] = v
    return out


def _save(data: dict[str, int]) -> None:
    DATA_FILE.write_text(
        json.dumps(dict(sorted(data.items())), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def add_stock(name: str, quantity: int) -> None:
    """Add quantity to a product. Creates the product if it does not exist."""
    name = name.strip()
    if not name:
        raise ValueError("Product name cannot be empty.")
    if quantity <= 0:
        raise ValueError("Quantity to add must be positive.")

    data = _load()
    data[name] = data.get(name, 0) + quantity
    _save(data)


def edit_product(
    current_name: str,
    *,
    new_name: str | None = None,
    add_quantity: int = 0,
    remove_quantity: int = 0,
) -> None:
    """
    Edit a product: optional rename, optional add/remove stock.
    At least one of new_name, add_quantity, or remove_quantity must change something.
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

    qty = data.pop(current_name) + add_quantity - remove_quantity
    if qty < 0:
        raise ValueError("Stock cannot be negative after this change.")

    if final_name != current_name and final_name in data:
        raise ValueError(f"A product named {final_name!r} already exists.")

    data[final_name] = qty
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


def list_products() -> list[tuple[str, int]]:
    """Return all products as (name, quantity), sorted by name."""
    data = _load()
    return sorted(data.items(), key=lambda x: x[0].lower())


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
                qty = _prompt_int("Quantity to add: ")
                add_stock(name, qty)
                print("Stock updated.")
            except (ValueError, KeyError) as e:
                print(f"Error: {e}")

        elif choice == "2":
            current = input("Current product name: ").strip()
            print("Leave blank to keep current name.")
            new_name = input("New name (optional): ").strip() or None
            add_s = input("Quantity to add (0 if none): ").strip() or "0"
            rem_s = input("Quantity to remove (0 if none): ").strip() or "0"
            try:
                add_q = int(add_s)
                rem_q = int(rem_s)
                edit_product(
                    current,
                    new_name=new_name,
                    add_quantity=add_q,
                    remove_quantity=rem_q,
                )
                print("Product updated.")
            except (ValueError, KeyError) as e:
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
                for n, q in items:
                    print(f"  {n}: {q}")

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

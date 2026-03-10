"""
Utility functions for InvenScan.
"""

import csv
import os
from typing import List, Dict, Tuple
from datetime import datetime


def export_to_csv(items: List[Dict], filepath: str = None) -> str:
    """
    Export inventory items to a CSV file.

    Args:
        items: List of inventory item dictionaries
        filepath: Optional custom filepath for export

    Returns:
        Path to the exported CSV file
    """
    if filepath is None:
        os.makedirs("exports", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = f"exports/inventory_export_{timestamp}.csv"

    # Ensure parent directory exists
    parent = os.path.dirname(filepath)
    if parent:
        os.makedirs(parent, exist_ok=True)

    columns = ["Title", "Price", "Quantity", "Condition", "Description",
               "Category", "Barcode", "Image Path"]

    with open(filepath, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=columns)
        writer.writeheader()

        for item in items:
            # Capitalize title as required
            title = item.get("title", "").upper()

            writer.writerow({
                "Title": title,
                "Price": item.get("price", 0.0),
                "Quantity": item.get("quantity", 0),
                "Condition": item.get("condition", ""),
                "Description": item.get("description", ""),
                "Category": item.get("category", ""),
                "Barcode": item.get("barcode", ""),
                "Image Path": item.get("image_path", ""),
            })

    return filepath


def validate_item_data(title: str, price: str, quantity: str) -> Tuple[bool, str]:
    """
    Validate item data before saving.

    Args:
        title: Item title
        price: Item price as string
        quantity: Item quantity as string

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not title or not title.strip():
        return False, "Title is required"

    try:
        price_float = float(price)
        if price_float < 0:
            return False, "Price must be non-negative"
    except ValueError:
        return False, "Price must be a valid number"

    try:
        quantity_int = int(quantity)
        if quantity_int < 0:
            return False, "Quantity must be non-negative"
    except ValueError:
        return False, "Quantity must be a valid integer"

    return True, ""


def format_price(price: float) -> str:
    """Format price for display."""
    return f"${price:.2f}"


def truncate_text(text: str, max_length: int = 50) -> str:
    """Truncate text to specified length with ellipsis."""
    if len(text) <= max_length:
        return text
    return text[: max_length - 3] + "..."

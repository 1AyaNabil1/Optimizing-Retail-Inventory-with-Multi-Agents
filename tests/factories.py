"""Builders for small in-memory versions of the three CSV datasets."""

import pandas as pd


def make_inventory(rows):
    """rows: (product_id, store_id, stock, reorder_point, warehouse_capacity)."""
    return pd.DataFrame(
        rows,
        columns=["Product ID", "Store ID", "Stock Levels", "Reorder Point", "Warehouse Capacity"],
    )


def make_demand(rows):
    """rows: (product_id, sales_quantity, demand_trend, customer_segment)."""
    return pd.DataFrame(
        rows, columns=["Product ID", "Sales Quantity", "Demand Trend", "Customer Segments"]
    )


def make_pricing(rows):
    """rows: (product_id, store_id, price, sales_volume)."""
    return pd.DataFrame(rows, columns=["Product ID", "Store ID", "Price", "Sales Volume"])

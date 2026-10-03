"""Locating and loading the CSV datasets used by the agents."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

DATA_DIR_ENV_VAR = "SMARTSTOCK_DATA_DIR"
DEFAULT_DATA_DIR = Path(__file__).resolve().parent.parent / "data"

DEMAND_FILE = "demand_forecasting.csv"
INVENTORY_FILE = "inventory_monitoring.csv"
PRICING_FILE = "pricing_optimization.csv"

# Columns each agent actually reads; checked up front so a wrong file fails
# with a clear message instead of a KeyError deep inside an agent.
REQUIRED_COLUMNS = {
    DEMAND_FILE: ["Product ID", "Sales Quantity", "Demand Trend", "Customer Segments"],
    INVENTORY_FILE: [
        "Product ID",
        "Store ID",
        "Stock Levels",
        "Reorder Point",
        "Warehouse Capacity",
    ],
    PRICING_FILE: ["Product ID", "Price", "Sales Volume"],
}


@dataclass
class Datasets:
    demand: pd.DataFrame
    inventory: pd.DataFrame
    pricing: pd.DataFrame


def resolve_data_dir(data_dir: str | os.PathLike[str] | None = None) -> Path:
    """Return the data directory.

    Precedence: explicit argument, then the ``SMARTSTOCK_DATA_DIR`` environment
    variable, then the repository's ``data/`` folder. The default is resolved
    relative to this file, so the code works from any working directory.
    """
    if data_dir is None:
        data_dir = os.environ.get(DATA_DIR_ENV_VAR) or DEFAULT_DATA_DIR
    return Path(data_dir).expanduser()


def read_dataset(path: str | os.PathLike[str]) -> pd.DataFrame:
    """Read one CSV and check that the columns the agents need are present."""
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(
            f"Dataset not found: {path}. Set {DATA_DIR_ENV_VAR} to the folder holding the CSVs."
        )
    # keep_default_na=False keeps literal category values such as "None"
    # (used in 'Seasonality Factors') instead of turning them into NaN.
    frame = pd.read_csv(path, keep_default_na=False, na_values=[""])
    missing = [c for c in REQUIRED_COLUMNS.get(path.name, []) if c not in frame.columns]
    if missing:
        raise ValueError(f"{path} is missing required columns: {missing}")
    return frame


def load_datasets(data_dir: str | os.PathLike[str] | None = None) -> Datasets:
    """Load the demand, inventory and pricing CSVs from ``data_dir``."""
    root = resolve_data_dir(data_dir)
    return Datasets(
        demand=read_dataset(root / DEMAND_FILE),
        inventory=read_dataset(root / INVENTORY_FILE),
        pricing=read_dataset(root / PRICING_FILE),
    )

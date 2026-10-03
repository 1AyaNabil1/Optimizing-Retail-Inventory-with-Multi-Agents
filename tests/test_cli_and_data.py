"""Command line entry point, data loading and the SQLite demo."""

import pandas as pd
import pytest

from Smart_Stock_Ai import data
from Smart_Stock_Ai.database import InventoryDB
from Smart_Stock_Ai.main import main


@pytest.fixture
def data_dir(tmp_path, small_datasets):
    """Write the small datasets as CSVs, like the real data/ folder."""
    small_datasets.demand.to_csv(tmp_path / data.DEMAND_FILE, index=False)
    small_datasets.inventory.to_csv(tmp_path / data.INVENTORY_FILE, index=False)
    small_datasets.pricing.to_csv(tmp_path / data.PRICING_FILE, index=False)
    return tmp_path


# --- CLI ---------------------------------------------------------------------


def test_cli_prints_summary_and_writes_history(data_dir, tmp_path, capsys):
    history_csv = tmp_path / "history.csv"
    exit_code = main(
        ["--data-dir", str(data_dir), "--steps", "4", "-q", "--history-csv", str(history_csv)]
    )
    out = capsys.readouterr().out
    assert exit_code == 0
    assert "Summary after 4 steps (seed=42)" in out
    assert "fill rate" in out
    history = pd.read_csv(history_csv)
    assert len(history) == 4 * 3
    assert set(history["product_id"]) == {101, 202, 303}


def test_cli_runs_against_bundled_data(capsys):
    assert main(["--steps", "2", "--quiet"]) == 0
    assert "4277" in capsys.readouterr().out


def test_cli_reports_bad_input_without_traceback(data_dir, capsys):
    assert main(["--data-dir", str(data_dir), "--product-ids", "999"]) == 1
    assert "error:" in capsys.readouterr().err
    assert main(["--data-dir", str(data_dir / "missing")]) == 1
    assert "Dataset not found" in capsys.readouterr().err


# --- data loading ------------------------------------------------------------


def test_data_dir_precedence(monkeypatch, tmp_path):
    monkeypatch.delenv(data.DATA_DIR_ENV_VAR, raising=False)
    assert data.resolve_data_dir() == data.DEFAULT_DATA_DIR
    monkeypatch.setenv(data.DATA_DIR_ENV_VAR, str(tmp_path))
    assert data.resolve_data_dir() == tmp_path
    assert data.resolve_data_dir("elsewhere") == data.Path("elsewhere")


def test_bundled_data_loads_from_any_working_directory(monkeypatch, tmp_path):
    monkeypatch.delenv(data.DATA_DIR_ENV_VAR, raising=False)
    monkeypatch.chdir(tmp_path)
    datasets = data.load_datasets()
    assert len(datasets.demand) == len(datasets.inventory) == len(datasets.pricing) == 10_000
    # The literal category "None" must survive loading instead of becoming NaN.
    assert "None" in set(datasets.demand["Seasonality Factors"])
    assert not datasets.demand["Seasonality Factors"].isna().any()


def test_missing_columns_are_reported(tmp_path):
    path = tmp_path / data.INVENTORY_FILE
    pd.DataFrame({"Product ID": [1], "Store ID": [1]}).to_csv(path, index=False)
    with pytest.raises(ValueError, match="Stock Levels"):
        data.read_dataset(path)


# --- SQLite demo -------------------------------------------------------------


def test_inventory_db_reads_and_updates_stock():
    db = InventoryDB()
    assert db.get_stock(9286, 16) == 700
    db.update_stock(9286, 16, 750)
    assert db.get_stock(9286, 16) == 750
    assert db.get_stock(1, 1) == 0  # unknown product/store


def test_inventory_db_accepts_custom_csv(data_dir):
    db = InventoryDB(data_dir / data.INVENTORY_FILE)
    assert db.get_stock(202, 2) == 500

"""The simulation loop: product selection, exact unit flows, invariants, seeds."""

import pytest

from Smart_Stock_Ai.data import load_datasets
from Smart_Stock_Ai.main import (
    InvariantViolation,
    SimulationConfig,
    check_invariants,
    run_smartstock_ai,
    select_products,
)


def run(datasets, **overrides):
    return run_smartstock_ai(SimulationConfig(**overrides), datasets=datasets)


def rows_for(history, product_id, column):
    return history.loc[history["product_id"] == product_id, column].tolist()


# --- product selection -------------------------------------------------------


def test_auto_selection_skips_products_without_inventory(small_datasets):
    d = small_datasets
    assert select_products(d.demand, d.inventory, 3) == [101, 202, 303]
    assert select_products(d.demand, d.inventory, 2) == [101, 202]


def test_explicit_products_are_validated_and_deduplicated(small_datasets):
    d = small_datasets
    assert select_products(d.demand, d.inventory, 1, [303, 101, 303]) == [303, 101]
    with pytest.raises(ValueError, match="999"):
        select_products(d.demand, d.inventory, 1, [999])


# --- exact, hand-computed run (no demand noise) -------------------------------


def test_deterministic_run_matches_hand_calculation(small_datasets):
    history = run(small_datasets, steps=3, demand_noise=0).history

    # 101: forecast 110, reorder point 20 -> first request 110 + 20 - 10, then
    # 110 per step to get back to the reorder point after selling 110.
    assert rows_for(history, 101, "request") == [120, 110, 110]
    assert rows_for(history, 101, "shipped") == [120, 110, 110]
    assert rows_for(history, 101, "store_stock_end") == [20, 20, 20]
    assert rows_for(history, 101, "warehouse_stock_end") == [880, 770, 660]
    assert rows_for(history, 101, "unmet") == [0, 0, 0]

    # 202: 500 on the shelf, forecast 18 -> never reorders.
    assert rows_for(history, 202, "request") == [0, 0, 0]
    assert rows_for(history, 202, "store_stock_end") == [482, 464, 446]

    # 303: warehouse capacity 50 cannot cover the 90-unit requests, so it ships
    # what it has and the supplier refills the shortfall for the next step.
    assert rows_for(history, 303, "shipped") == [50, 40, 50]
    assert rows_for(history, 303, "supplier_delivered") == [40, 50, 40]
    assert rows_for(history, 303, "sold") == [50, 40, 50]
    assert rows_for(history, 303, "unmet") == [30, 40, 30]
    assert rows_for(history, 303, "warehouse_stock_end") == [40, 50, 40]


def test_summary_totals(small_datasets):
    summary = run(small_datasets, steps=3, demand_noise=0).summary.set_index("product")
    row = summary.loc[303]
    assert (row["demand"], row["sold"], row["unmet"]) == (240, 140, 100)
    assert row["stockout_steps"] == 3
    assert row["delivered"] == 130
    assert (row["store_end"], row["wh_end"]) == (0, 40)
    assert summary.loc[101, "fill_rate"] == 1.0


def test_slow_mover_discount_applied_once_without_mutating_input(small_datasets):
    result = run(small_datasets, steps=4, demand_noise=0)
    prices = result.pricing.set_index(["Product ID", "Store ID"])["Price"]
    assert prices[(202, 2)] == pytest.approx(18.0)  # one 10% cut, not 0.9**4
    assert prices[(202, 9)] == pytest.approx(99.0)  # other store untouched
    assert prices[(101, 1)] == pytest.approx(10.0)  # fast mover, never discounted
    assert small_datasets.pricing["Price"].tolist() == [10.0, 20.0, 99.0]


# --- invariants --------------------------------------------------------------


def assert_invariants(history, summary):
    assert (history["store_stock_end"] >= 0).all()
    assert (history["warehouse_stock_end"] >= 0).all()
    assert (history["sold"] <= history["demand"]).all()
    assert (history["sold"] + history["unmet"] == history["demand"]).all()
    assert (history["shipped"] <= history["request"]).all()
    # Store flow each step: start + received - sold = end.
    assert (
        history["store_stock_start"] + history["shipped"] - history["sold"]
        == history["store_stock_end"]
    ).all()
    # Warehouse flow each step: previous end - shipped + delivered = end.
    for _, group in history.groupby("product_id"):
        previous = group["warehouse_stock_end"].shift(1).iloc[1:]
        current = group.iloc[1:]
        assert (
            previous - current["shipped"] + current["supplier_delivered"]
            == current["warehouse_stock_end"]
        ).all()
    # Whole-run conservation: no units created or lost.
    for _, row in summary.iterrows():
        assert (
            row["store_end"] + row["wh_end"]
            == row["store_start"] + row["wh_start"] + row["delivered"] - row["sold"]
        )


@pytest.mark.parametrize("seed", [0, 1, 2])
def test_invariants_hold_on_bundled_data(seed):
    result = run_smartstock_ai(
        SimulationConfig(steps=20, num_products=10, seed=seed, demand_noise=0.5)
    )
    assert len(result.history) == 20 * 10
    assert_invariants(result.history, result.summary)


def test_invariants_hold_on_small_data_with_noise(small_datasets):
    result = run(small_datasets, steps=15, demand_noise=0.4, seed=3)
    assert_invariants(result.history, result.summary)


def test_check_invariants_flags_violations():
    check_invariants(1, store_stock=5, warehouse_stock=5, initial_total=10, delivered=3, sold=3)
    with pytest.raises(InvariantViolation, match="Negative"):
        check_invariants(1, -1, 11, 10, 0, 0)
    with pytest.raises(InvariantViolation, match="conserved"):
        check_invariants(1, 5, 6, 10, 0, 0)


# --- reproducibility ---------------------------------------------------------


def test_same_seed_gives_identical_runs(small_datasets):
    first = run(small_datasets, steps=10, seed=123).history
    second = run(small_datasets, steps=10, seed=123).history
    assert first.equals(second)


def test_different_seeds_give_different_demand(small_datasets):
    first = run(small_datasets, steps=10, seed=1).history
    second = run(small_datasets, steps=10, seed=2).history
    assert first["demand"].tolist() != second["demand"].tolist()


def test_zero_noise_makes_demand_equal_forecast(small_datasets):
    history = run(small_datasets, steps=5, demand_noise=0).history
    assert (history["demand"] == history["forecast"]).all()


def test_default_run_on_bundled_data_is_reproducible():
    datasets = load_datasets()
    first = run_smartstock_ai(datasets=datasets)
    second = run_smartstock_ai(datasets=datasets)
    assert first.summary["product"].tolist() == [4277, 5540, 5406]
    assert first.history.equals(second.history)


# --- configuration -----------------------------------------------------------


@pytest.mark.parametrize(
    "bad",
    [{"steps": 0}, {"num_products": 0}, {"demand_noise": -0.1}, {"delay": -1}],
)
def test_invalid_config_is_rejected(bad):
    with pytest.raises(ValueError):
        SimulationConfig(**bad)

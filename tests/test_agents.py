"""Decision rules of the individual agents."""

import pytest

from Smart_Stock_Ai.customer_agent import CustomerAgent
from Smart_Stock_Ai.demand_agent import DemandAgent
from Smart_Stock_Ai.store_agent import StoreAgent
from Smart_Stock_Ai.supplier_agent import SupplierAgent
from Smart_Stock_Ai.warehouse_agent import WarehouseAgent

from .factories import make_demand, make_inventory, make_pricing

# --- DemandAgent -------------------------------------------------------------


@pytest.mark.parametrize(
    ("trend", "sales", "expected"),
    [
        ("Increasing", 330, 363),  # 330 * 1.1
        ("Decreasing", 429, 386),  # 429 * 0.9 = 386.1 -> whole units
        ("Stable", 298, 298),
        ("Unknown", 298, 298),  # unrecognised trend -> no adjustment
    ],
)
def test_demand_forecast_applies_trend_multiplier(trend, sales, expected):
    agent = DemandAgent(make_demand([(1, sales, trend, "Regular")]))
    assert agent.predict_demand(1) == expected


def test_demand_forecast_uses_first_record_for_product():
    agent = DemandAgent(make_demand([(1, 100, "Stable", "R"), (1, 999, "Stable", "R")]))
    assert agent.predict_demand(1) == 100


def test_demand_forecast_unknown_product_raises_readable_error():
    agent = DemandAgent(make_demand([(1, 100, "Stable", "R")]))
    with pytest.raises(KeyError, match="Product 42 not found in demand data"):
        agent.predict_demand(42)


# --- StoreAgent: reorder rule ------------------------------------------------


def store(stock, reorder_point):
    return StoreAgent(make_inventory([(1, 7, stock, reorder_point, 1000)]))


def test_store_requests_nothing_when_stock_covers_demand_and_reorder_point():
    agent = store(stock=200, reorder_point=50)
    assert agent.check_stock(1, 100) == 0  # 200 - 100 = 100 >= 50


def test_store_does_not_reorder_exactly_at_reorder_point():
    agent = store(stock=150, reorder_point=50)
    assert agent.check_stock(1, 100) == 0  # 150 - 100 = 50, not below 50


def test_store_reorders_up_to_demand_plus_reorder_point():
    agent = store(stock=120, reorder_point=50)
    # 120 - 100 = 20 < 50 -> request 100 + 50 - 120
    assert agent.check_stock(1, 100) == 30
    assert agent.request == 30
    assert agent.last_request[1] == 30


def test_store_rule_with_zero_reorder_point_matches_original_stock_below_demand_rule():
    agent = store(stock=10, reorder_point=0)
    assert agent.check_stock(1, 363) == 353  # original prototype: demand - stock
    assert store(stock=363, reorder_point=0).check_stock(1, 363) == 0


def test_store_check_stock_does_not_change_stock():
    agent = store(stock=10, reorder_point=5)
    agent.check_stock(1, 100)
    assert agent.get_stock(1) == 10


def test_store_rejects_negative_demand():
    with pytest.raises(ValueError):
        store(10, 5).check_stock(1, -1)


def test_store_unknown_product_raises_readable_error():
    with pytest.raises(KeyError, match="Product 2 not found in inventory data"):
        store(10, 5).check_stock(2, 1)


# --- StoreAgent: stock movements ---------------------------------------------


def test_store_sell_never_goes_negative_and_reports_units_sold():
    agent = store(stock=30, reorder_point=0)
    assert agent.sell(1, 50) == 30
    assert agent.get_stock(1) == 0
    assert agent.sell(1, 5) == 0
    assert agent.get_stock(1) == 0


def test_store_sell_within_stock():
    agent = store(stock=30, reorder_point=0)
    assert agent.sell(1, 12) == 12
    assert agent.get_stock(1) == 18


def test_store_receive_adds_stock_and_rejects_negative_quantities():
    agent = store(stock=30, reorder_point=0)
    agent.receive(1, 20)
    assert agent.get_stock(1) == 50
    with pytest.raises(ValueError):
        agent.receive(1, -5)
    with pytest.raises(ValueError):
        agent.sell(1, -5)


# --- StoreAgent: pricing -----------------------------------------------------


def test_slow_mover_discounted_once_and_only_on_evaluated_row():
    agent = store(stock=500, reorder_point=0)
    pricing = make_pricing([(1, 7, 20.0, 40), (1, 9, 99.0, 40), (2, 7, 5.0, 10)])
    agent.check_stock(1, 10)  # no request -> slow-moving candidate

    pricing = agent.adjust_pricing(pricing, 1)
    pricing = agent.adjust_pricing(pricing, 1)  # must not compound

    assert pricing["Price"].tolist() == pytest.approx([18.0, 99.0, 5.0])


def test_no_discount_when_store_needed_replenishment():
    agent = store(stock=5, reorder_point=0)
    pricing = make_pricing([(1, 7, 20.0, 40)])
    agent.check_stock(1, 10)
    assert agent.adjust_pricing(pricing, 1)["Price"].tolist() == [20.0]


def test_no_discount_for_fast_movers():
    agent = store(stock=500, reorder_point=0)
    pricing = make_pricing([(1, 7, 20.0, 100)])  # threshold is < 100
    agent.check_stock(1, 10)
    assert agent.adjust_pricing(pricing, 1)["Price"].tolist() == [20.0]


def test_missing_pricing_data_is_skipped():
    agent = store(stock=500, reorder_point=0)
    pricing = make_pricing([(2, 7, 20.0, 10)])
    agent.check_stock(1, 10)
    assert agent.adjust_pricing(pricing, 1)["Price"].tolist() == [20.0]


# --- WarehouseAgent ----------------------------------------------------------


def warehouse(capacity):
    return WarehouseAgent(make_inventory([(1, 7, 0, 0, capacity)]))


def test_warehouse_starts_full_because_capacity_is_the_stock_proxy():
    assert warehouse(300).get_stock(1) == 300


def test_warehouse_fills_request_from_stock():
    agent = warehouse(300)
    assert agent.handle_request(1, 120) == 120
    assert agent.get_stock(1) == 180
    assert agent.needs_restock == 0


def test_warehouse_ships_what_it_has_and_orders_shortfall():
    agent = warehouse(100)
    assert agent.handle_request(1, 150) == 100
    assert agent.get_stock(1) == 0
    assert agent.needs_restock == 50


def test_warehouse_supplier_order_is_capped_by_capacity():
    agent = warehouse(100)
    assert agent.handle_request(1, 500) == 100
    assert agent.needs_restock == 100  # shortfall 400, but only 100 units of space


def test_warehouse_restock_signal_resets_between_requests():
    # Regression: needs_restock used to stay set, so the supplier kept
    # restocking the same quantity on every later step.
    agent = warehouse(100)
    agent.handle_request(1, 150)
    agent.receive(1, agent.needs_restock)
    assert agent.handle_request(1, 0) == 0
    assert agent.needs_restock == 0
    assert agent.handle_request(1, 10) == 10
    assert agent.needs_restock == 0


def test_warehouse_rejects_deliveries_beyond_capacity_and_negative_quantities():
    agent = warehouse(100)
    agent.handle_request(1, 30)
    agent.receive(1, 30)
    assert agent.get_stock(1) == 100
    with pytest.raises(ValueError, match="capacity"):
        agent.receive(1, 1)
    with pytest.raises(ValueError):
        agent.receive(1, -1)
    with pytest.raises(ValueError):
        agent.handle_request(1, -1)


# --- SupplierAgent and CustomerAgent -----------------------------------------


def test_supplier_delivers_exactly_what_is_asked():
    supplier = SupplierAgent()
    assert supplier.restock(40, product_id=1) == 40
    assert supplier.restock(0) == 0
    with pytest.raises(ValueError):
        supplier.restock(-1)


def test_customer_agent_reports_segment_and_trend():
    agent = CustomerAgent(make_demand([(1, 10, "Increasing", "Premium")]))
    assert agent.update_behavior(1) == ("Premium", "Increasing")
    assert agent.update_behavior(2) is None

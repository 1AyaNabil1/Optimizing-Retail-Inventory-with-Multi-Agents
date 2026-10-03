"""Small, hand-checkable datasets shared by the tests."""

import pytest

from Smart_Stock_Ai.data import Datasets

from .factories import make_demand, make_inventory, make_pricing


@pytest.fixture
def small_datasets():
    """Three products with different stock situations.

    101: low shelf stock, large warehouse   -> store must reorder every step
    202: plenty of shelf stock, slow seller -> no reorder, discount candidate
    303: low shelf stock, tiny warehouse    -> warehouse runs dry, supplier steps in
    999: demand data only (no inventory)    -> must be skipped, not crash
    """
    demand = make_demand(
        [
            (999, 50, "Stable", "Budget"),
            (101, 100, "Increasing", "Regular"),
            (202, 20, "Decreasing", "Premium"),
            (303, 80, "Stable", "Budget"),
            (101, 5, "Stable", "Budget"),  # later duplicate row: ignored
        ]
    )
    inventory = make_inventory(
        [
            (101, 1, 10, 20, 1000),
            (202, 2, 500, 50, 300),
            (303, 3, 0, 10, 50),
        ]
    )
    pricing = make_pricing(
        [
            (101, 1, 10.0, 400),
            (202, 2, 20.0, 40),
            (202, 9, 99.0, 40),
        ]
    )
    return Datasets(demand=demand, inventory=inventory, pricing=pricing)

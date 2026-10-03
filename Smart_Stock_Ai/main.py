# main.py
"""Run the SmartStock AI simulation.

    python -m Smart_Stock_Ai.main --steps 5 --products 3 --seed 42

Each step, for every selected product, the agents act in this order:

1. DemandAgent forecasts demand.
2. StoreAgent compares shelf stock with the forecast and its reorder point,
   and requests units from the warehouse.
3. WarehouseAgent ships what it can; any shortfall becomes a supplier order.
4. SupplierAgent delivers that order to the warehouse.
5. CustomerAgent reports the product's customer segment and trend.
6. Customers buy: actual demand is the forecast plus seeded random noise, and
   the store sells what it has on the shelf.
7. StoreAgent discounts slow-moving products.
"""

import argparse
import logging
import sys
import time
from dataclasses import dataclass

import numpy as np
import pandas as pd

from Smart_Stock_Ai.customer_agent import CustomerAgent
from Smart_Stock_Ai.data import DATA_DIR_ENV_VAR, load_datasets
from Smart_Stock_Ai.demand_agent import DemandAgent
from Smart_Stock_Ai.store_agent import StoreAgent
from Smart_Stock_Ai.supplier_agent import SupplierAgent
from Smart_Stock_Ai.warehouse_agent import WarehouseAgent

logger = logging.getLogger(__name__)


@dataclass
class SimulationConfig:
    steps: int = 5
    num_products: int = 3
    product_ids: list[int] | None = None  # overrides num_products when given
    seed: int = 42
    demand_noise: float = 0.2  # std-dev of actual demand as a fraction of the forecast
    data_dir: str | None = None
    delay: float = 0.0  # seconds to pause between steps (for live demos)

    def __post_init__(self):
        if self.steps < 1:
            raise ValueError("steps must be >= 1")
        if self.num_products < 1:
            raise ValueError("num_products must be >= 1")
        if self.demand_noise < 0:
            raise ValueError("demand_noise must be >= 0")
        if self.delay < 0:
            raise ValueError("delay must be >= 0")


@dataclass
class SimulationResult:
    history: pd.DataFrame  # one row per (step, product)
    summary: pd.DataFrame  # one row per product
    pricing: pd.DataFrame  # pricing data after the store's adjustments


class InvariantViolation(RuntimeError):
    """Raised when stock goes negative or units appear/disappear."""


def select_products(demand_data, inventory_data, num_products, product_ids=None):
    """Pick the products to simulate.

    Explicit ``product_ids`` must exist in both the demand and the inventory
    data. Otherwise the first ``num_products`` distinct products of the demand
    data that also have inventory data are used (products without inventory
    rows used to crash the loop).
    """
    demand_ids = set(demand_data["Product ID"])
    inventory_ids = set(inventory_data["Product ID"])
    if product_ids:
        missing = [p for p in product_ids if p not in demand_ids or p not in inventory_ids]
        if missing:
            raise ValueError(f"Products not found in both demand and inventory data: {missing}")
        return [int(p) for p in dict.fromkeys(product_ids)]

    selected = []
    for product_id in demand_data["Product ID"].drop_duplicates():
        if product_id in inventory_ids:
            selected.append(int(product_id))
            if len(selected) == num_products:
                break
    if not selected:
        raise ValueError("No product appears in both the demand and the inventory data")
    return selected


def sample_demand(rng, expected, noise):
    """Actual customer demand: the forecast plus normal noise, as whole units >= 0."""
    if noise == 0 or expected == 0:
        return int(expected)
    return max(0, round(rng.normal(expected, noise * expected)))


def check_invariants(product_id, store_stock, warehouse_stock, initial_total, delivered, sold):
    """Stock is never negative and units are conserved across store and warehouse."""
    if store_stock < 0 or warehouse_stock < 0:
        raise InvariantViolation(
            f"Negative stock for product {product_id}: "
            f"store={store_stock}, warehouse={warehouse_stock}"
        )
    expected = initial_total + delivered - sold
    if store_stock + warehouse_stock != expected:
        raise InvariantViolation(
            f"Units not conserved for product {product_id}: store + warehouse = "
            f"{store_stock + warehouse_stock}, expected {expected}"
        )


def summarize(history, initial_stock):
    """Per-product totals from the step history."""
    rows = []
    for product_id, group in history.groupby("product_id", sort=False):
        last = group.iloc[-1]
        demand = int(group["demand"].sum())
        sold = int(group["sold"].sum())
        store_start, warehouse_start = initial_stock[product_id]
        rows.append(
            {
                "product": product_id,
                "store_start": store_start,
                "wh_start": warehouse_start,
                "demand": demand,
                "sold": sold,
                "unmet": demand - sold,
                "fill_rate": round(sold / demand, 3) if demand else 1.0,
                "stockout_steps": int((group["unmet"] > 0).sum()),
                "shipped": int(group["shipped"].sum()),
                "delivered": int(group["supplier_delivered"].sum()),
                "store_end": int(last["store_stock_end"]),
                "wh_end": int(last["warehouse_stock_end"]),
            }
        )
    return pd.DataFrame(rows)


def run_smartstock_ai(config=None, datasets=None):
    """Run the simulation and return its step history and per-product summary.

    Runs are reproducible: the same config (including ``seed``) and data give
    identical results.
    """
    config = config or SimulationConfig()
    datasets = datasets or load_datasets(config.data_dir)
    logger.info("Starting SmartStock AI Simulation...")

    rng = np.random.default_rng(config.seed)
    pricing_data = datasets.pricing.copy()  # never mutate the caller's data

    # Initialize agents with data
    demand_agent = DemandAgent(datasets.demand)
    store_agent = StoreAgent(datasets.inventory)
    warehouse_agent = WarehouseAgent(datasets.inventory)
    supplier_agent = SupplierAgent()
    customer_agent = CustomerAgent(datasets.demand)

    products = select_products(
        datasets.demand, datasets.inventory, config.num_products, config.product_ids
    )
    initial_stock = {p: (store_agent.get_stock(p), warehouse_agent.get_stock(p)) for p in products}
    delivered_total = dict.fromkeys(products, 0)
    sold_total = dict.fromkeys(products, 0)
    records = []

    for step in range(1, config.steps + 1):
        for product_id in products:
            store_stock_start = store_agent.get_stock(product_id)
            forecast = demand_agent.predict_demand(product_id)
            request = store_agent.check_stock(product_id, forecast)
            shipped = warehouse_agent.handle_request(product_id, request)
            store_agent.receive(product_id, shipped)
            delivered = supplier_agent.restock(warehouse_agent.needs_restock, product_id)
            warehouse_agent.receive(product_id, delivered)
            customer_agent.update_behavior(product_id)
            demand = sample_demand(rng, forecast, config.demand_noise)
            sold = store_agent.sell(product_id, demand)
            pricing_data = store_agent.adjust_pricing(pricing_data, product_id)

            delivered_total[product_id] += delivered
            sold_total[product_id] += sold
            store_stock_end = store_agent.get_stock(product_id)
            warehouse_stock_end = warehouse_agent.get_stock(product_id)
            check_invariants(
                product_id,
                store_stock_end,
                warehouse_stock_end,
                sum(initial_stock[product_id]),
                delivered_total[product_id],
                sold_total[product_id],
            )
            records.append(
                {
                    "step": step,
                    "product_id": product_id,
                    "store_id": store_agent.store_ids[product_id],
                    "forecast": forecast,
                    "store_stock_start": store_stock_start,
                    "request": request,
                    "shipped": shipped,
                    "supplier_delivered": delivered,
                    "demand": demand,
                    "sold": sold,
                    "unmet": demand - sold,
                    "store_stock_end": store_stock_end,
                    "warehouse_stock_end": warehouse_stock_end,
                }
            )
        logger.info(f"--- Time Step {step} Complete ---")
        if config.delay:
            time.sleep(config.delay)  # Pause for readability

    history = pd.DataFrame(records)
    return SimulationResult(
        history=history, summary=summarize(history, initial_stock), pricing=pricing_data
    )


def build_parser():
    defaults = SimulationConfig()
    parser = argparse.ArgumentParser(
        prog="python -m Smart_Stock_Ai.main",
        description="Rule-based multi-agent retail inventory simulation.",
    )
    parser.add_argument("--steps", type=int, default=defaults.steps, help="time steps to run")
    parser.add_argument(
        "--products",
        type=int,
        default=defaults.num_products,
        help="number of products (first ones in the demand data that have inventory data)",
    )
    parser.add_argument(
        "--product-ids", type=int, nargs="+", help="simulate these product IDs instead"
    )
    parser.add_argument("--seed", type=int, default=defaults.seed, help="random seed")
    parser.add_argument(
        "--demand-noise",
        type=float,
        default=defaults.demand_noise,
        help="std-dev of actual demand as a fraction of the forecast (0 = demand equals forecast)",
    )
    parser.add_argument(
        "--data-dir",
        help=f"folder with the CSVs (default: ${DATA_DIR_ENV_VAR} or the repo's data/)",
    )
    parser.add_argument(
        "--delay", type=float, default=defaults.delay, help="seconds to pause between steps"
    )
    parser.add_argument("--history-csv", help="write the per-step history to this CSV file")
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="agent log verbosity (logs go to stderr)",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="only print the summary (same as --log-level WARNING)",
    )
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    logging.basicConfig(
        level="WARNING" if args.quiet else args.log_level, format="%(message)s", force=True
    )
    try:
        config = SimulationConfig(
            steps=args.steps,
            num_products=args.products,
            product_ids=args.product_ids,
            seed=args.seed,
            demand_noise=args.demand_noise,
            data_dir=args.data_dir,
            delay=args.delay,
        )
        result = run_smartstock_ai(config)
    except (FileNotFoundError, ValueError, KeyError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.history_csv:
        result.history.to_csv(args.history_csv, index=False)

    summary = result.summary
    total_demand = int(summary["demand"].sum())
    total_sold = int(summary["sold"].sum())
    steps_label = "step" if config.steps == 1 else "steps"
    print(f"Summary after {config.steps} {steps_label} (seed={config.seed}):")
    print(summary.to_string(index=False))
    if total_demand:
        print(
            f"Total: demand {total_demand}, sold {total_sold}, "
            f"fill rate {total_sold / total_demand:.1%}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())

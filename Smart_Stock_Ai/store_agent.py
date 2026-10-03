# store_agent.py
import logging

from Smart_Stock_Ai.data import first_row

logger = logging.getLogger(__name__)

DISCOUNT_RATE = 0.10
SLOW_SALES_VOLUME = 100  # 'Sales Volume' below this counts as slow-moving


class StoreAgent:
    """Store shelf stock per product, seeded from inventory_monitoring.csv.

    Each product uses its first row in the inventory data ('Stock Levels',
    'Reorder Point', 'Store ID'). Stock changes only through receive() and
    sell(), so it can never go negative.
    """

    def __init__(self, inventory_data):
        self.inventory_data = inventory_data
        self.stock = {}
        self.reorder_points = {}
        self.store_ids = {}
        self.request = 0  # most recent request, kept for backwards compatibility
        self.last_request = {}
        self.discounted_products = set()  # discount at most once per product per run

    def _ensure_loaded(self, product_id):
        if product_id not in self.stock:
            product_data = first_row(self.inventory_data, product_id, "inventory")
            self.stock[product_id] = int(product_data["Stock Levels"])
            self.reorder_points[product_id] = int(product_data["Reorder Point"])
            self.store_ids[product_id] = int(product_data["Store ID"])

    def get_stock(self, product_id):
        self._ensure_loaded(product_id)
        return self.stock[product_id]

    def check_stock(self, product_id, demand):
        """Return how many units to request from the warehouse.

        Reorder rule: if the stock left after the forecast demand would drop
        below the product's reorder point, request enough to cover the forecast
        and end the step at the reorder point:

            request = max(0, demand + reorder_point - stock)

        With a reorder point of 0 this is the original "stock < demand" rule.
        """
        if demand < 0:
            raise ValueError(f"demand must be >= 0, got {demand}")
        stock = self.get_stock(product_id)
        reorder_point = self.reorder_points[product_id]
        store_id = self.store_ids[product_id]
        logger.info(
            f"StoreAgent: Product {product_id} at Store {store_id} - Stock = {stock}, "
            f"Demand = {demand}, Reorder point = {reorder_point}"
        )
        if stock - demand < reorder_point:
            request = demand + reorder_point - stock
            logger.info(f"StoreAgent: Requesting {request} units from Warehouse")
        else:
            request = 0
            logger.info("StoreAgent: Stock sufficient")
        self.request = request
        self.last_request[product_id] = request
        return request

    def receive(self, product_id, quantity):
        if quantity < 0:
            raise ValueError(f"quantity must be >= 0, got {quantity}")
        self.stock[product_id] = self.get_stock(product_id) + quantity

    def sell(self, product_id, demand):
        """Sell up to ``demand`` units from shelf stock; return the units sold."""
        if demand < 0:
            raise ValueError(f"demand must be >= 0, got {demand}")
        stock = self.get_stock(product_id)
        sold = min(stock, demand)
        self.stock[product_id] = stock - sold
        if sold < demand:
            logger.info(
                f"StoreAgent: Product {product_id} - Stockout, sold {sold} of {demand} units "
                f"({demand - sold} unmet)"
            )
        else:
            logger.info(f"StoreAgent: Product {product_id} - Sold {sold} units")
        return sold

    def adjust_pricing(self, pricing_data, product_id):
        """Discount slow-moving products once; return the (updated) pricing data.

        A product is slow-moving when its last stock check needed no
        replenishment and its 'Sales Volume' is below 100.
        """
        product_pricing = pricing_data[pricing_data["Product ID"] == product_id]
        if not product_pricing.empty:
            row_index = product_pricing.index[0]
            product_pricing = product_pricing.iloc[0]
            no_request = self.last_request.get(product_id, 0) == 0
            slow_moving = no_request and product_pricing["Sales Volume"] < SLOW_SALES_VOLUME
            if slow_moving and product_id not in self.discounted_products:
                new_price = product_pricing["Price"] * (1 - DISCOUNT_RATE)
                logger.info(
                    f"StoreAgent: Product {product_id} - Adjusted price to {new_price:.2f} "
                    "due to slow sales"
                )
                # Update only the row the decision was based on; other stores'
                # rows for the same product keep their own prices.
                pricing_data.loc[row_index, "Price"] = new_price
                self.discounted_products.add(product_id)
        else:
            logger.info(
                f"StoreAgent: Product {product_id} - No pricing data available, skipping adjustment"
            )
        return pricing_data

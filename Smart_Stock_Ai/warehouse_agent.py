# warehouse_agent.py
import logging

from Smart_Stock_Ai.data import first_row

logger = logging.getLogger(__name__)


class WarehouseAgent:
    """Warehouse stock per product.

    The dataset has no warehouse on-hand column, so (as in the original
    prototype) a product's 'Warehouse Capacity' is used both as its initial
    warehouse stock and as the most the warehouse can hold.
    """

    def __init__(self, inventory_data):
        self.inventory_data = inventory_data
        self.stock = {}
        self.capacity = {}
        self.needs_restock = 0  # supplier order produced by the latest request

    def _ensure_loaded(self, product_id):
        if product_id not in self.stock:
            product_data = first_row(self.inventory_data, product_id, "inventory")
            capacity = int(product_data["Warehouse Capacity"])  # Using capacity as stock proxy
            self.capacity[product_id] = capacity
            self.stock[product_id] = capacity

    def get_stock(self, product_id):
        self._ensure_loaded(product_id)
        return self.stock[product_id]

    def handle_request(self, product_id, request):
        """Ship what is on hand towards ``request``; return the units shipped.

        If the request cannot be filled completely, ``needs_restock`` is set to
        the shortfall (capped by free capacity) for the supplier to deliver.
        """
        # Reset every call: a shortfall from an earlier request must not make the
        # supplier restock again when this request is zero or fully served.
        self.needs_restock = 0
        if request < 0:
            raise ValueError(f"request must be >= 0, got {request}")
        if request == 0:
            return 0
        on_hand = self.get_stock(product_id)
        shipped = min(request, on_hand)
        self.stock[product_id] = on_hand - shipped
        logger.info(f"WarehouseAgent: Product {product_id} - Sent {shipped} units to Store")
        shortfall = request - shipped
        if shortfall > 0:
            free_space = self.capacity[product_id] - self.stock[product_id]
            self.needs_restock = min(shortfall, free_space)
            logger.info(
                f"WarehouseAgent: Product {product_id} - Low stock! "
                f"Need {self.needs_restock} units from Supplier"
            )
        return shipped

    def receive(self, product_id, quantity):
        if quantity < 0:
            raise ValueError(f"quantity must be >= 0, got {quantity}")
        on_hand = self.get_stock(product_id)
        free_space = self.capacity[product_id] - on_hand
        if quantity > free_space:
            raise ValueError(
                f"Receiving {quantity} units of product {product_id} would exceed "
                f"warehouse capacity ({free_space} units free)"
            )
        self.stock[product_id] = on_hand + quantity

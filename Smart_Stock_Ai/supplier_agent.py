# supplier_agent.py
import logging

logger = logging.getLogger(__name__)


class SupplierAgent:
    """Supplier with unlimited stock that delivers immediately.

    Supplier lead times in the dataset are not modelled.
    """

    def restock(self, needs_restock, product_id=None):
        """Deliver the requested quantity to the warehouse; return units delivered."""
        if needs_restock < 0:
            raise ValueError(f"needs_restock must be >= 0, got {needs_restock}")
        label = f" of Product {product_id}" if product_id is not None else ""
        if needs_restock > 0:
            logger.info(f"SupplierAgent: Restocking {needs_restock} units{label} to Warehouse")
        else:
            logger.info("SupplierAgent: No restock needed")
        return needs_restock

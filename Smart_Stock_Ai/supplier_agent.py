# supplier_agent.py
import logging

logger = logging.getLogger(__name__)

class SupplierAgent:
    def restock(self, needs_restock):
        if needs_restock > 0:
            logger.info(f"SupplierAgent: Restocking {needs_restock:.2f} units to Warehouse")
        else:
            logger.info("SupplierAgent: No restock needed")
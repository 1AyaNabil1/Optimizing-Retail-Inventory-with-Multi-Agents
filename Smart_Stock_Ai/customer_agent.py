# customer_agent.py
import logging

from Smart_Stock_Ai.data import first_row

logger = logging.getLogger(__name__)


class CustomerAgent:
    """Reports the customer segment and demand trend recorded for a product.

    Informational only: its output does not feed into any other agent's decision.
    """

    def __init__(self, demand_data):
        self.demand_data = demand_data

    def update_behavior(self, product_id):
        try:
            product_data = first_row(self.demand_data, product_id, "demand")
        except KeyError:
            logger.info(f"CustomerAgent: Product {product_id} - No customer data")
            return None
        segment = product_data["Customer Segments"]
        trend = product_data["Demand Trend"]
        logger.info(f"CustomerAgent: Product {product_id} - Segment = {segment}, Trend = {trend}")
        return segment, trend

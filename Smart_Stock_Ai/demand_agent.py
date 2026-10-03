# demand_agent.py
import logging

from Smart_Stock_Ai.data import first_row

logger = logging.getLogger(__name__)

# Multiplier applied to the recorded sales quantity for each demand trend.
TREND_MULTIPLIERS = {"Increasing": 1.1, "Decreasing": 0.9, "Stable": 1.0}


class DemandAgent:
    """Rule-based demand forecast from demand_forecasting.csv.

    forecast = Sales Quantity x trend multiplier (1.1 increasing, 0.9
    decreasing, 1.0 otherwise), rounded to whole units, using the first
    record for the product.
    """

    def __init__(self, demand_data):
        self.demand_data = demand_data

    def predict_demand(self, product_id):
        product_data = first_row(self.demand_data, product_id, "demand")
        trend = TREND_MULTIPLIERS.get(product_data["Demand Trend"], 1.0)
        predicted_demand = round(float(product_data["Sales Quantity"]) * trend)
        logger.info(f"DemandAgent: Product {product_id} - Predicted demand = {predicted_demand} units")
        return predicted_demand

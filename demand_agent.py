# demand_agent.py
class DemandAgent:
    def __init__(self, demand_data):
        self.demand_data = demand_data

    def predict_demand(self, product_id):
        # Filter data for product
        product_data = self.demand_data[self.demand_data["Product ID"] == product_id].iloc[0]
        sales = product_data["Sales Quantity"]
        trend = 1.1 if product_data["Demand Trend"] == "Increasing" else (0.9 if product_data["Demand Trend"] == "Decreasing" else 1.0)
        predicted_demand = sales * trend  # Simple trend-based forecast
        print(f"DemandAgent: Product {product_id} - Predicted demand = {predicted_demand:.2f} units")
        return predicted_demand
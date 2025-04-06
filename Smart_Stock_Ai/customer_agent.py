# customer_agent.py
class CustomerAgent:
    def __init__(self, demand_data):
        self.demand_data = demand_data

    def update_behavior(self, product_id):
        product_data = self.demand_data[self.demand_data["Product ID"] == product_id].iloc[0]
        segment = product_data["Customer Segments"]
        trend = product_data["Demand Trend"]
        print(f"CustomerAgent: Product {product_id} - Segment = {segment}, Trend = {trend}")
# store_agent.py
class StoreAgent:
    def __init__(self, inventory_data):
        self.inventory_data = inventory_data
        self.request = 0

    def check_stock(self, product_id, demand):
        product_data = self.inventory_data[self.inventory_data["Product ID"] == product_id].iloc[0]
        stock = product_data["Stock Levels"]
        store_id = product_data["Store ID"]
        print(f"StoreAgent: Product {product_id} at Store {store_id} - Stock = {stock}, Demand = {demand:.2f}")
        if stock < demand:
            self.request = demand - stock
            print(f"StoreAgent: Requesting {self.request:.2f} units from Warehouse")
        else:
            self.request = 0
            print("StoreAgent: Stock sufficient")

    def adjust_pricing(self, pricing_data, product_id):
        product_pricing = pricing_data[pricing_data["Product ID"] == product_id].iloc[0]
        if self.request == 0 and product_pricing["Sales Volume"] < 100:  # Slow-moving stock
            new_price = product_pricing["Price"] * 0.9  # 10% discount
            print(f"StoreAgent: Product {product_id} - Adjusted price to {new_price:.2f} due to slow sales")
            pricing_data.loc[pricing_data["Product ID"] == product_id, "Price"] = new_price
        return pricing_data
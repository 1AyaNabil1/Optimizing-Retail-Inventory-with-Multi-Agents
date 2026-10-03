# store_agent.py
class StoreAgent:
    def __init__(self, inventory_data):
        self.inventory_data = inventory_data
        self.request = 0
        self.discounted_products = set()  # discount at most once per product per run

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
        # Check if product exists in pricing data
        product_pricing = pricing_data[pricing_data["Product ID"] == product_id]
        if not product_pricing.empty:
            row_index = product_pricing.index[0]
            product_pricing = product_pricing.iloc[0]
            slow_moving = self.request == 0 and product_pricing["Sales Volume"] < 100
            if slow_moving and product_id not in self.discounted_products:
                new_price = product_pricing["Price"] * 0.9  # 10% discount
                print(f"StoreAgent: Product {product_id} - Adjusted price to {new_price:.2f} due to slow sales")
                # Update only the row the decision was based on; other stores'
                # rows for the same product keep their own prices.
                pricing_data.loc[row_index, "Price"] = new_price
                self.discounted_products.add(product_id)
        else:
            print(f"StoreAgent: Product {product_id} - No pricing data available, skipping adjustment")
        return pricing_data
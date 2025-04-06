# warehouse_agent.py
class WarehouseAgent:
    def __init__(self, inventory_data):
        self.inventory_data = inventory_data
        self.needs_restock = 0

    def handle_request(self, product_id, request):
        if request > 0:
            product_data = self.inventory_data[self.inventory_data["Product ID"] == product_id].iloc[0]
            warehouse_stock = product_data["Warehouse Capacity"]  # Using capacity as stock proxy
            if warehouse_stock >= request:
                print(f"WarehouseAgent: Product {product_id} - Sent {request:.2f} units to Store")
            else:
                self.needs_restock = request - warehouse_stock
                print(f"WarehouseAgent: Product {product_id} - Low stock! Need {self.needs_restock:.2f} units from Supplier")
# main.py
from Smart_Stock_Ai.data import load_datasets
from Smart_Stock_Ai.demand_agent import DemandAgent
from Smart_Stock_Ai.store_agent import StoreAgent
from Smart_Stock_Ai.warehouse_agent import WarehouseAgent
from Smart_Stock_Ai.supplier_agent import SupplierAgent
from Smart_Stock_Ai.customer_agent import CustomerAgent
import time

def run_smartstock_ai():
    print("Starting SmartStock AI Simulation...")
    
    # Load datasets from data/ (or $SMARTSTOCK_DATA_DIR) using
    # portable paths; the old Windows-style "data\\..." strings failed on
    # macOS and Linux.
    datasets = load_datasets()
    demand_data = datasets.demand
    inventory_data = datasets.inventory
    pricing_data = datasets.pricing

    # Initialize agents with data
    demand_agent = DemandAgent(demand_data)
    store_agent = StoreAgent(inventory_data)
    warehouse_agent = WarehouseAgent(inventory_data)
    supplier_agent = SupplierAgent()
    customer_agent = CustomerAgent(demand_data)

    # Simulate 3 time steps
    for step in range(3):
        product_id = demand_data.iloc[step]["Product ID"]  # Pick a product
        demand = demand_agent.predict_demand(product_id)
        store_agent.check_stock(product_id, demand)
        warehouse_agent.handle_request(product_id, store_agent.request)
        supplier_agent.restock(warehouse_agent.needs_restock)
        customer_agent.update_behavior(product_id)
        pricing_data = store_agent.adjust_pricing(pricing_data, product_id)
        time.sleep(1)  # Pause for readability
        print(f"--- Time Step {step + 1} Complete ---")

if __name__ == "__main__":
    run_smartstock_ai()
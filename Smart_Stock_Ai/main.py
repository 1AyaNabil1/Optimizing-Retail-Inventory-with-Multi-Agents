# main.py
import pandas as pd
from Smart_Stock_Ai.demand_agent import DemandAgent
from Smart_Stock_Ai.store_agent import StoreAgent
from Smart_Stock_Ai.warehouse_agent import WarehouseAgent
from Smart_Stock_Ai.supplier_agent import SupplierAgent
from Smart_Stock_Ai.customer_agent import CustomerAgent
import time

def run_smartstock_ai():
    print("Starting SmartStock AI Simulation...")
    
    # Load datasets with corrected paths
    demand_data = pd.read_csv(r"data\demand_forecasting.csv")
    inventory_data = pd.read_csv(r"data\inventory_monitoring.csv")
    pricing_data = pd.read_csv(r"data\pricing_optimization.csv")

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
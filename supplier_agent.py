# supplier_agent.py
class SupplierAgent:
    def restock(self, needs_restock):
        if needs_restock > 0:
            print(f"SupplierAgent: Restocking {needs_restock:.2f} units to Warehouse")
        else:
            print("SupplierAgent: No restock needed")
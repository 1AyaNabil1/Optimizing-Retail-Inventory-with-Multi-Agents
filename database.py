# database.py
import sqlite3
import pandas as pd

class InventoryDB:
    def __init__(self):
        self.conn = sqlite3.connect(":memory:")  # In-memory DB
        self.cursor = self.conn.cursor()
        self.cursor.execute("CREATE TABLE inventory (product_id INTEGER, store_id INTEGER, stock REAL)")
        # Load initial data
        inventory_data = pd.read_csv("Inventory Monitoring.csv")
        for _, row in inventory_data.iterrows():
            self.cursor.execute("INSERT INTO inventory VALUES (?, ?, ?)",
                               (row["Product ID"], row["Store ID"], row["Stock Levels"]))
        self.conn.commit()

    def update_stock(self, product_id, store_id, stock):
        self.cursor.execute("UPDATE inventory SET stock = ? WHERE product_id = ? AND store_id = ?",
                           (stock, product_id, store_id))
        self.conn.commit()
        print(f"Database: Updated Product {product_id} at Store {store_id} to stock = {stock}")

    def get_stock(self, product_id, store_id):
        self.cursor.execute("SELECT stock FROM inventory WHERE product_id = ? AND store_id = ?",
                           (product_id, store_id))
        result = self.cursor.fetchone()
        return result[0] if result else 0

# Demo usage
if __name__ == "__main__":
    db = InventoryDB()
    print(f"Initial stock for Product 9286 at Store 16: {db.get_stock(9286, 16)}")
    db.update_stock(9286, 16, 750)
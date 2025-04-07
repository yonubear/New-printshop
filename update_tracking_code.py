"""
Add tracking code to Order model

This script adds the tracking_code column to the Order table for dynamic QR code generation.
"""
import logging
import sqlite3
from app import app
import os

def update_order_table():
    """Add tracking_code column to order table"""
    # Get database connection
    db_path = os.path.join(app.instance_path, 'printshop.db')
    
    if not os.path.exists(db_path):
        logging.error(f"Database file {db_path} does not exist.")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if column already exists
        cursor.execute("PRAGMA table_info(order)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        if 'tracking_code' not in column_names:
            cursor.execute("ALTER TABLE 'order' ADD COLUMN tracking_code TEXT")
            # Add a unique index as a separate step
            cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_order_tracking_code ON 'order' (tracking_code)")
            conn.commit()
            logging.info("Added tracking_code column to Order table successfully.")
            print("Added tracking_code column to Order table successfully.")
        else:
            logging.info("tracking_code column already exists in Order table.")
            print("tracking_code column already exists in Order table.")
        
        conn.close()
        return True
    except sqlite3.Error as e:
        logging.error(f"SQLite error: {e}")
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    update_order_table()
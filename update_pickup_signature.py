"""
Update database to add pickup signature fields to Order model
"""
import os
import sys
import sqlite3
from datetime import datetime


def migrate_pickup_signature_fields():
    """Add pickup signature fields to Order table"""
    print("Connecting to database...")
    # Connect directly to SQLite database in the instance folder
    conn = sqlite3.connect('instance/printshop.db')
    cursor = conn.cursor()
    
    # Check if the fields already exist
    cursor.execute("PRAGMA table_info(\"order\")")
    columns = [column[1] for column in cursor.fetchall()]
    print(f"Existing columns: {columns}")
    
    # For SQLite, we need to add columns without constraints
    if 'pickup_date' not in columns:
        print("Adding pickup_date column to order table...")
        cursor.execute("ALTER TABLE \"order\" ADD COLUMN pickup_date TIMESTAMP")
        
    if 'pickup_signature' not in columns:
        print("Adding pickup_signature column to order table...")
        cursor.execute("ALTER TABLE \"order\" ADD COLUMN pickup_signature TEXT")
        
    if 'pickup_signature_name' not in columns:
        print("Adding pickup_signature_name column to order table...")
        cursor.execute("ALTER TABLE \"order\" ADD COLUMN pickup_signature_name VARCHAR(100)")
        
    if 'pickup_by' not in columns:
        print("Adding pickup_by column to order table...")
        cursor.execute("ALTER TABLE \"order\" ADD COLUMN pickup_by VARCHAR(100)")
        
    if 'is_picked_up' not in columns:
        print("Adding is_picked_up column to order table...")
        cursor.execute("ALTER TABLE \"order\" ADD COLUMN is_picked_up BOOLEAN DEFAULT 0")

    # Commit changes and close the connection
    conn.commit()
    conn.close()
    print("Migration completed!")

if __name__ == "__main__":
    migrate_pickup_signature_fields()
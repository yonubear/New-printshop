#!/usr/bin/env python3
"""
Add Order Item Material Table

This script creates the missing item_material table in the database
and adds any necessary relationships between order_items and materials.

Usage:
    python add_order_item_material_table.py
"""

import os
import sys
from datetime import datetime
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_database_connection():
    """Connect to the PostgreSQL database using environment variables."""
    conn_params = {
        'dbname': os.environ.get('PGDATABASE'),
        'user': os.environ.get('PGUSER'),
        'password': os.environ.get('PGPASSWORD'),
        'host': os.environ.get('PGHOST'),
        'port': os.environ.get('PGPORT'),
    }
    
    try:
        conn = psycopg2.connect(**conn_params)
        return conn
    except psycopg2.Error as e:
        print(f"Error connecting to PostgreSQL database: {e}")
        sys.exit(1)

def check_table_exists(conn, table_name):
    """Check if a table exists in the database."""
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT EXISTS (
                   SELECT FROM information_schema.tables 
                   WHERE table_name = %s
                );
            """, (table_name,))
            return cursor.fetchone()[0]
    except psycopg2.Error as e:
        print(f"Error checking if table exists: {e}")
        return False

def create_material_table(conn):
    """Create the item_material table if it doesn't exist."""
    if check_table_exists(conn, 'item_material'):
        print("The item_material table already exists.")
        return
    
    try:
        with conn.cursor() as cursor:
            # Create the item_material table
            cursor.execute("""
                CREATE TABLE item_material (
                    id SERIAL PRIMARY KEY,
                    order_item_id INTEGER NOT NULL REFERENCES order_item(id) ON DELETE CASCADE,
                    material_name VARCHAR(100) NOT NULL,
                    quantity FLOAT DEFAULT 0.0,
                    unit VARCHAR(20) DEFAULT 'pcs',
                    notes TEXT,
                    category VARCHAR(50),
                    saved_price_id INTEGER REFERENCES saved_price(id),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Create indexes for better performance
            cursor.execute("CREATE INDEX idx_item_material_order_item_id ON item_material(order_item_id);")
            
            conn.commit()
            print("Successfully created the item_material table.")
    except psycopg2.Error as e:
        conn.rollback()
        print(f"Error creating item_material table: {e}")
        sys.exit(1)

def main():
    """Main function to add the item_material table."""
    print("Adding item_material table...")
    
    conn = get_database_connection()
    
    try:
        # Create the item_material table
        create_material_table(conn)
        
        print("Successfully added the item_material table.")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
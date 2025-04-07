#!/usr/bin/env python3
"""
Diagnose Item Materials

This script diagnoses issues with order item materials in the database
and fixes any association problems between order_items and materials.

Usage:
    python diagnose_item_materials.py [--fix]
"""

import os
import sys
import argparse
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
        conn.autocommit = False  # Ensure we use transactions
        return conn
    except psycopg2.Error as e:
        print(f"Error connecting to PostgreSQL database: {e}")
        sys.exit(1)

def check_tables(conn):
    """Check if the item_material table exists and has the correct structure."""
    try:
        with conn.cursor() as cursor:
            # Check if the item_material table exists
            cursor.execute("""
                SELECT EXISTS (
                   SELECT FROM information_schema.tables 
                   WHERE table_name = 'item_material'
                );
            """)
            exists = cursor.fetchone()[0]
            
            if not exists:
                print("ERROR: The item_material table doesn't exist!")
                return False
            
            # Check if the item_material table has the correct columns
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'item_material'
                ORDER BY ordinal_position;
            """)
            columns = [row[0] for row in cursor.fetchall()]
            
            required_columns = ['id', 'order_item_id', 'material_name', 'quantity', 'unit', 'notes', 'category', 'saved_price_id']
            
            for col in required_columns:
                if col not in columns:
                    print(f"ERROR: The item_material table is missing the '{col}' column!")
                    return False
                    
            print("The item_material table exists and has the correct structure.")
            return True
            
    except psycopg2.Error as e:
        print(f"Error checking tables: {e}")
        return False

def check_associations(conn):
    """Check if order_items are properly associated with materials."""
    try:
        with conn.cursor() as cursor:
            # Get count of order items
            cursor.execute("SELECT COUNT(*) FROM order_item;")
            order_item_count = cursor.fetchone()[0]
            
            # Get count of materials
            cursor.execute("SELECT COUNT(*) FROM item_material;")
            material_count = cursor.fetchone()[0]
            
            print(f"Found {order_item_count} order items and {material_count} materials.")
            
            # Check for order items with materials
            cursor.execute("""
                SELECT COUNT(DISTINCT order_item_id) 
                FROM item_material;
            """)
            items_with_materials = cursor.fetchone()[0]
            
            print(f"Found {items_with_materials} order items that have materials associated with them.")
            
            # If no materials, check for saved prices
            if material_count == 0:
                cursor.execute("SELECT COUNT(*) FROM saved_price WHERE category = 'material';")
                saved_materials = cursor.fetchone()[0]
                print(f"Found {saved_materials} saved materials that could be associated with items.")
            
            return order_item_count, material_count, items_with_materials
            
    except psycopg2.Error as e:
        print(f"Error checking associations: {e}")
        return 0, 0, 0

def add_test_material(conn, fix=False):
    """Add a test material to verify item_material table functionality."""
    if not fix:
        print("Would add a test material if --fix was specified.")
        return
    
    try:
        with conn.cursor() as cursor:
            # Get first order item
            cursor.execute("SELECT id FROM order_item LIMIT 1;")
            result = cursor.fetchone()
            
            if not result:
                print("No order items found to add a test material to.")
                return
                
            order_item_id = result[0]
            
            # Check if there's already a test material for this item
            cursor.execute("""
                SELECT COUNT(*) FROM item_material 
                WHERE order_item_id = %s AND material_name = 'Test Material';
            """, (order_item_id,))
            has_test_material = cursor.fetchone()[0] > 0
            
            if has_test_material:
                print(f"Order item {order_item_id} already has a test material.")
                return
            
            # Add a test material
            cursor.execute("""
                INSERT INTO item_material (
                    order_item_id, material_name, quantity, unit, notes, category
                ) VALUES (
                    %s, 'Test Material', 1, 'pcs', 'Added for testing', 'other'
                );
            """, (order_item_id,))
            
            conn.commit()
            print(f"Successfully added a test material to order item {order_item_id}.")
        
    except psycopg2.Error as e:
        conn.rollback()
        print(f"Error adding test material: {e}")

def fix_foreign_keys(conn, fix=False):
    """Fix any foreign key constraints on the item_material table."""
    if not fix:
        print("Would fix foreign key constraints if --fix was specified.")
        return
    
    try:
        with conn.cursor() as cursor:
            # Check if foreign keys exist
            cursor.execute("""
                SELECT COUNT(*)
                FROM information_schema.table_constraints tc
                JOIN information_schema.constraint_column_usage ccu
                ON tc.constraint_name = ccu.constraint_name
                WHERE tc.constraint_type = 'FOREIGN KEY' 
                AND tc.table_name = 'item_material' 
                AND ccu.table_name = 'order_item';
            """)
            has_foreign_key = cursor.fetchone()[0] > 0
            
            if has_foreign_key:
                print("Foreign key for order_item_id already exists.")
            else:
                print("Adding foreign key constraint for order_item_id...")
                cursor.execute("""
                    ALTER TABLE item_material 
                    ADD CONSTRAINT fk_item_material_order_item
                    FOREIGN KEY (order_item_id) 
                    REFERENCES order_item(id)
                    ON DELETE CASCADE;
                """)
            
            # Check if foreign key for saved_price_id exists
            cursor.execute("""
                SELECT COUNT(*)
                FROM information_schema.table_constraints tc
                JOIN information_schema.constraint_column_usage ccu
                ON tc.constraint_name = ccu.constraint_name
                WHERE tc.constraint_type = 'FOREIGN KEY' 
                AND tc.table_name = 'item_material' 
                AND ccu.table_name = 'saved_price';
            """)
            has_saved_price_fk = cursor.fetchone()[0] > 0
            
            if has_saved_price_fk:
                print("Foreign key for saved_price_id already exists.")
            else:
                print("Adding foreign key constraint for saved_price_id...")
                cursor.execute("""
                    ALTER TABLE item_material 
                    ADD CONSTRAINT fk_item_material_saved_price
                    FOREIGN KEY (saved_price_id) 
                    REFERENCES saved_price(id)
                    ON DELETE SET NULL;
                """)
            
            conn.commit()
            print("Successfully fixed foreign key constraints.")
        
    except psycopg2.Error as e:
        conn.rollback()
        print(f"Error fixing foreign keys: {e}")

def main():
    """Main function to diagnose and fix item materials."""
    parser = argparse.ArgumentParser(description='Diagnose order item materials in the database')
    parser.add_argument('--fix', action='store_true', help='Apply fixes for any issues found')
    args = parser.parse_args()
    
    print("Diagnosing order item materials...")
    
    conn = get_database_connection()
    
    try:
        # Check tables
        tables_ok = check_tables(conn)
        if not tables_ok:
            print("The item_material table structure is not correct!")
        
        # Check associations
        order_items, materials, with_materials = check_associations(conn)
        
        # Add a test material to verify functionality
        add_test_material(conn, args.fix)
        
        # Fix foreign keys if needed
        fix_foreign_keys(conn, args.fix)
        
        if args.fix:
            print("Fixes have been applied.")
        else:
            print("Run with --fix to apply suggested fixes.")
        
    finally:
        conn.close()

if __name__ == "__main__":
    main()
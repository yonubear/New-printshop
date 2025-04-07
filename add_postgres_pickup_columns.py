#!/usr/bin/env python3
"""
Add PostgreSQL Pickup Columns

This script directly adds missing pickup-related columns to the database
without using SQLAlchemy. This approach is more reliable for reserved keywords.

Usage:
    python add_postgres_pickup_columns.py
"""

import os
import sys
from dotenv import load_dotenv
import psycopg2

# Load environment variables
load_dotenv()

def add_postgres_pickup_columns():
    """Add missing pickup columns to PostgreSQL database"""
    # Get database connection string from environment
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("Error: DATABASE_URL environment variable not set.")
        return False
    
    print(f"Database URL: {database_url}")
    
    # Check if this is a PostgreSQL database
    if not database_url.startswith('postgresql://'):
        print("Error: This script is intended for PostgreSQL databases only.")
        print(f"Current DATABASE_URL: {database_url}")
        return False
    
    try:
        # Connect to PostgreSQL database
        conn = psycopg2.connect(database_url)
        conn.autocommit = False
        cursor = conn.cursor()
        
        # Check existing columns first
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_schema = 'public' AND table_name = 'order'
        """)
        
        columns = [col[0] for col in cursor.fetchall()]
        print(f"Found {len(columns)} columns in order table:")
        for col in columns:
            print(f"  - {col}")
        
        # Columns to add
        pickup_columns = [
            ('is_picked_up', 'BOOLEAN DEFAULT FALSE'),
            ('pickup_date', 'TIMESTAMP'),
            ('pickup_by', 'VARCHAR(100)'),
            ('pickup_signature', 'TEXT'),
            ('pickup_signature_name', 'VARCHAR(100)'),
            ('tracking_code', 'VARCHAR(100) UNIQUE')
        ]
        
        # Add missing columns
        for col_name, col_type in pickup_columns:
            if col_name in columns:
                print(f"Column '{col_name}' already exists.")
                continue
                
            print(f"Adding column '{col_name}' ({col_type})...")
            try:
                cursor.execute(f'ALTER TABLE "order" ADD COLUMN {col_name} {col_type}')
                print(f"✅ Added column '{col_name}'")
            except Exception as e:
                print(f"Error adding column '{col_name}': {e}")
                conn.rollback()
                conn.close()
                return False
                
        # Force a refresh of PG catalog statistics
        cursor.execute("ANALYZE \"order\"")
        print("\nRefreshed PostgreSQL table statistics.")
        
        # Test query with is_picked_up column
        print("\nTesting a query with is_picked_up column:")
        try:
            cursor.execute('SELECT id, order_number, is_picked_up FROM "order" LIMIT 1')
            result = cursor.fetchone()
            if result:
                print(f"  ✅ Query successful: {result}")
            else:
                print("  ✅ Query successful but no rows returned")
        except Exception as e:
            print(f"  ❌ Query failed: {e}")
            
        # Commit changes
        conn.commit()
        print("\n✅ Changes committed successfully.")
        
        # Close connection
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"\nError updating database: {e}")
        if 'conn' in locals() and conn:
            conn.rollback()
            conn.close()
        return False

if __name__ == "__main__":
    print("=== Add PostgreSQL Pickup Columns ===")
    if add_postgres_pickup_columns():
        print("\nDatabase update completed successfully.")
        print("Please restart your application.")
    else:
        print("\nDatabase update failed. Please check the error messages above.")
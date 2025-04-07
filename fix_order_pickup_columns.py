#!/usr/bin/env python3
"""
Fix Order Pickup Columns

This script directly adds the missing pickup columns to the order table using raw SQL queries.
It's designed to work with your existing database connection and avoid SQLAlchemy conflicts.
"""

import os
import sys
from dotenv import load_dotenv
import psycopg2

def main():
    """Add missing pickup columns directly to the order table."""
    # Load environment variables
    load_dotenv()
    
    # Get database connection info
    db_url = os.environ.get('DATABASE_URL')
    
    if not db_url:
        print("No DATABASE_URL found in environment variables.")
        # Try individual connection parameters
        host = os.environ.get('PGHOST', 'localhost')
        port = os.environ.get('PGPORT', '5432')
        dbname = os.environ.get('PGDATABASE', 'printshop')
        user = os.environ.get('PGUSER', 'postgres')
        password = os.environ.get('PGPASSWORD', '')
        
        # Construct connection string
        db_url = f"postgresql://{user}:{password}@{host}:{port}/{dbname}"
    
    print(f"Connecting to database...")
    
    try:
        # Connect to database
        conn = psycopg2.connect(db_url)
        conn.autocommit = False
        cursor = conn.cursor()
        
        # First check if columns exist
        print("Checking existing columns...")
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_schema = 'public' AND table_name = 'order'
        """)
        existing_columns = [row[0] for row in cursor.fetchall()]
        print(f"Found {len(existing_columns)} columns in order table")
        
        # Define the columns to add
        columns_to_add = [
            {"name": "is_picked_up", "type": "BOOLEAN", "default": "false"},
            {"name": "pickup_date", "type": "TIMESTAMP", "default": "NULL"},
            {"name": "pickup_by", "type": "VARCHAR(100)", "default": "NULL"},
            {"name": "pickup_signature", "type": "TEXT", "default": "NULL"},
            {"name": "pickup_signature_name", "type": "VARCHAR(100)", "default": "NULL"},
            {"name": "tracking_code", "type": "VARCHAR(50)", "default": "NULL"}
        ]
        
        # Add each missing column
        for column in columns_to_add:
            if column["name"] not in existing_columns:
                default_clause = f"DEFAULT {column['default']}" if column["default"] != "NULL" else ""
                sql = f'ALTER TABLE "order" ADD COLUMN {column["name"]} {column["type"]} {default_clause}'
                print(f"Adding column: {column['name']} ({column['type']})")
                cursor.execute(sql)
            else:
                print(f"Column {column['name']} already exists")
        
        # Create indexes if they don't exist
        print("Creating indexes...")
        indexes = [
            {"name": "idx_order_customer_id", "column": "customer_id"},
            {"name": "idx_order_status", "column": "status"},
            {"name": "idx_order_tracking_code", "column": "tracking_code"}
        ]
        
        for index in indexes:
            cursor.execute(f"""
                SELECT 1 FROM pg_indexes 
                WHERE schemaname = 'public' 
                AND tablename = 'order' 
                AND indexname = '{index["name"]}'
            """)
            if not cursor.fetchone():
                print(f"Creating index {index['name']} on {index['column']}")
                cursor.execute(f'CREATE INDEX {index["name"]} ON "order" ({index["column"]})')
            else:
                print(f"Index {index['name']} already exists")
        
        # Verify the columns were added
        cursor.execute("""
            SELECT column_name, data_type
            FROM information_schema.columns 
            WHERE table_schema = 'public' AND table_name = 'order'
            AND column_name IN ('is_picked_up', 'pickup_date', 'pickup_by', 'pickup_signature', 'pickup_signature_name', 'tracking_code')
        """)
        added_columns = cursor.fetchall()
        
        if added_columns:
            print("\nSuccessfully added the following columns:")
            for col_name, col_type in added_columns:
                print(f"- {col_name} ({col_type})")
        else:
            print("\nWARNING: No pickup columns were found after attempted addition.")
        
        # Try a test query
        print("\nTesting with a query...")
        try:
            cursor.execute('SELECT id, is_picked_up FROM "order" LIMIT 1')
            test_result = cursor.fetchone()
            print(f"Test query successful: {test_result}")
        except Exception as e:
            print(f"Test query failed: {e}")
            print("This suggests the column still has issues.")
        
        # Commit the changes
        conn.commit()
        print("\nChanges committed to database.")
        
        return True
    
    except Exception as e:
        print(f"Error: {e}")
        if 'conn' in locals() and conn:
            conn.rollback()
            print("Changes rolled back.")
        return False
    
    finally:
        if 'conn' in locals() and conn:
            conn.close()
            print("Database connection closed.")

if __name__ == "__main__":
    print("Fix Order Pickup Columns Script")
    print("===============================")
    
    result = main()
    
    if result:
        print("\n✅ Script completed successfully")
        print("Please restart your Flask application to pick up the changes.")
    else:
        print("\n❌ Script failed to complete")
        print("Please check the error messages above.")
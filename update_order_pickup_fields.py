#!/usr/bin/env python3
"""
Update Order Table with Pickup Fields

This script adds the missing pickup-related columns to the Order table
for existing Print Shop Management System installations.

Usage:
    python update_order_pickup_fields.py
"""

import os
import sys
import sqlite3
from pathlib import Path
from urllib.parse import urlparse

# Try to import dotenv and psycopg2, but don't fail if not available
try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False
    print("Warning: python-dotenv not installed. Using environment variables as is.")

try:
    import psycopg2
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False
    print("Warning: psycopg2 not installed. PostgreSQL support is disabled.")

# Load environment variables if dotenv is available
if DOTENV_AVAILABLE:
    load_dotenv()

def get_sqlite_path(database_url):
    """Extract SQLite database path from database URL"""
    # Remove sqlite:/// prefix
    if database_url.startswith('sqlite:///'):
        db_path = database_url[10:]
        # Handle relative paths
        if not os.path.isabs(db_path):
            # For Flask-style instance/db.sqlite paths
            if db_path.startswith('instance/'):
                return db_path
            # For plain relative paths
            return os.path.join('instance', db_path)
        return db_path
    return None

def update_sqlite_order_table(db_path):
    """Add pickup-related columns to SQLite Order table"""
    try:
        # Ensure path exists
        if not os.path.exists(os.path.dirname(db_path)):
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            print(f"Created directory: {os.path.dirname(db_path)}")
            
        # Check if database file exists
        if not os.path.exists(db_path):
            print(f"Error: Database file not found: {db_path}")
            return False
            
        # Connect to SQLite database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if Order table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='order'")
        if not cursor.fetchone():
            print("Error: Order table does not exist.")
            conn.close()
            return False
            
        # Get existing columns
        cursor.execute("PRAGMA table_info(\"order\")")
        columns = [col[1] for col in cursor.fetchall()]
        
        # Add is_picked_up column if it doesn't exist
        if 'is_picked_up' not in columns:
            print("Adding is_picked_up column to Order table...")
            cursor.execute('ALTER TABLE "order" ADD COLUMN is_picked_up BOOLEAN DEFAULT 0')
            print("✅ Added is_picked_up column")
        else:
            print("✅ is_picked_up column already exists")
            
        # Add pickup_date column if it doesn't exist
        if 'pickup_date' not in columns:
            print("Adding pickup_date column to Order table...")
            cursor.execute('ALTER TABLE "order" ADD COLUMN pickup_date TIMESTAMP')
            print("✅ Added pickup_date column")
        else:
            print("✅ pickup_date column already exists")
            
        # Add pickup_by column if it doesn't exist
        if 'pickup_by' not in columns:
            print("Adding pickup_by column to Order table...")
            cursor.execute('ALTER TABLE "order" ADD COLUMN pickup_by VARCHAR(100)')
            print("✅ Added pickup_by column")
        else:
            print("✅ pickup_by column already exists")
            
        # Add pickup_signature column if it doesn't exist
        if 'pickup_signature' not in columns:
            print("Adding pickup_signature column to Order table...")
            cursor.execute('ALTER TABLE "order" ADD COLUMN pickup_signature TEXT')
            print("✅ Added pickup_signature column")
        else:
            print("✅ pickup_signature column already exists")
            
        # Add pickup_signature_name column if it doesn't exist
        if 'pickup_signature_name' not in columns:
            print("Adding pickup_signature_name column to Order table...")
            cursor.execute('ALTER TABLE "order" ADD COLUMN pickup_signature_name VARCHAR(100)')
            print("✅ Added pickup_signature_name column")
        else:
            print("✅ pickup_signature_name column already exists")
            
        # Add tracking_code column if it doesn't exist
        if 'tracking_code' not in columns:
            print("Adding tracking_code column to Order table...")
            cursor.execute('ALTER TABLE "order" ADD COLUMN tracking_code VARCHAR(100) UNIQUE')
            print("✅ Added tracking_code column")
        else:
            print("✅ tracking_code column already exists")
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error updating SQLite database: {e}")
        if 'conn' in locals() and conn:
            conn.close()
        return False

def update_postgres_order_table(database_url):
    """Add pickup-related columns to PostgreSQL Order table"""
    if not PSYCOPG2_AVAILABLE:
        print("Error: psycopg2 not installed. Cannot update PostgreSQL database.")
        return False
        
    try:
        # Connect to PostgreSQL database
        conn = psycopg2.connect(database_url)
        conn.autocommit = False
        cursor = conn.cursor()
        
        # Check if Order table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_name = 'order'
            )
        """)
        table_exists = cursor.fetchone()[0]
        if not table_exists:
            print("Error: Order table does not exist.")
            conn.close()
            return False
        
        # Get all columns in the order table
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_schema = 'public' AND table_name = 'order'
        """)
        columns = [row[0] for row in cursor.fetchall()]
        
        # Add is_picked_up column if it doesn't exist
        if 'is_picked_up' not in columns:
            print("Adding is_picked_up column to Order table...")
            cursor.execute('ALTER TABLE "order" ADD COLUMN is_picked_up BOOLEAN DEFAULT FALSE')
            print("✅ Added is_picked_up column")
        else:
            print("✅ is_picked_up column already exists")
            
        # Add pickup_date column if it doesn't exist
        if 'pickup_date' not in columns:
            print("Adding pickup_date column to Order table...")
            cursor.execute('ALTER TABLE "order" ADD COLUMN pickup_date TIMESTAMP')
            print("✅ Added pickup_date column")
        else:
            print("✅ pickup_date column already exists")
            
        # Add pickup_by column if it doesn't exist
        if 'pickup_by' not in columns:
            print("Adding pickup_by column to Order table...")
            cursor.execute('ALTER TABLE "order" ADD COLUMN pickup_by VARCHAR(100)')
            print("✅ Added pickup_by column")
        else:
            print("✅ pickup_by column already exists")
            
        # Add pickup_signature column if it doesn't exist
        if 'pickup_signature' not in columns:
            print("Adding pickup_signature column to Order table...")
            cursor.execute('ALTER TABLE "order" ADD COLUMN pickup_signature TEXT')
            print("✅ Added pickup_signature column")
        else:
            print("✅ pickup_signature column already exists")
            
        # Add pickup_signature_name column if it doesn't exist
        if 'pickup_signature_name' not in columns:
            print("Adding pickup_signature_name column to Order table...")
            cursor.execute('ALTER TABLE "order" ADD COLUMN pickup_signature_name VARCHAR(100)')
            print("✅ Added pickup_signature_name column")
        else:
            print("✅ pickup_signature_name column already exists")
            
        # Add tracking_code column if it doesn't exist
        if 'tracking_code' not in columns:
            print("Adding tracking_code column to Order table...")
            cursor.execute('ALTER TABLE "order" ADD COLUMN tracking_code VARCHAR(100) UNIQUE')
            print("✅ Added tracking_code column")
        else:
            print("✅ tracking_code column already exists")
            
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error updating PostgreSQL database: {e}")
        if 'conn' in locals() and conn:
            conn.rollback()
            conn.close()
        return False

def update_order_table():
    """Add pickup-related columns to Order table"""
    # Get database connection string from environment
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("Error: DATABASE_URL environment variable not set.")
        return False
    
    print(f"Database URL: {database_url}")
    
    # Check database type
    if database_url.startswith('postgresql://'):
        print("Detected PostgreSQL database.")
        return update_postgres_order_table(database_url)
    elif database_url.startswith('sqlite:///'):
        print("Detected SQLite database.")
        db_path = get_sqlite_path(database_url)
        print(f"SQLite database path: {db_path}")
        return update_sqlite_order_table(db_path)
    else:
        print(f"Error: Unsupported database type: {database_url}")
        print("This script supports PostgreSQL and SQLite databases.")
        return False

if __name__ == "__main__":
    print("=== Order Table Pickup Fields Update ===")
    if update_order_table():
        print("\nUpdate completed successfully.")
        sys.exit(0)
    else:
        print("\nUpdate failed. Please check the error messages above.")
        sys.exit(1)
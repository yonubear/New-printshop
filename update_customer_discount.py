#!/usr/bin/env python3
"""
Update Customer Discount Feature

This script adds the discount_percentage column to the customer table
for existing Print Shop Management System installations.

Supports both SQLite and PostgreSQL databases.

Usage:
    python update_customer_discount.py
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

def update_sqlite_customer_table(db_path):
    """Add discount_percentage column to SQLite customer table"""
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
        
        # Check if customer table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='customer'")
        if not cursor.fetchone():
            print("Error: Customer table does not exist.")
            conn.close()
            return False
            
        # Check if the column already exists
        cursor.execute("PRAGMA table_info(customer)")
        columns = cursor.fetchall()
        column_exists = any(col[1] == 'discount_percentage' for col in columns)
        
        # Column already exists
        if column_exists:
            print("✅ Customer discount_percentage column already exists.")
            conn.close()
            return True
        
        # Add the column
        print("Adding discount_percentage column to customer table...")
        cursor.execute("ALTER TABLE customer ADD COLUMN discount_percentage REAL DEFAULT 0.0")
        conn.commit()
        print("✅ Customer discount feature added successfully!")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error updating SQLite database: {e}")
        if 'conn' in locals() and conn:
            conn.close()
        return False

def update_postgres_customer_table(database_url):
    """Add discount_percentage column to PostgreSQL customer table"""
    if not PSYCOPG2_AVAILABLE:
        print("Error: psycopg2 not installed. Cannot update PostgreSQL database.")
        return False
        
    try:
        # Connect to PostgreSQL database
        conn = psycopg2.connect(database_url)
        conn.autocommit = False
        cursor = conn.cursor()
        
        # Check if customer table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_name = 'customer'
            )
        """)
        table_exists = cursor.fetchone()[0]
        if not table_exists:
            print("Error: Customer table does not exist.")
            conn.close()
            return False
        
        # Check if the column already exists
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_schema = 'public' AND table_name = 'customer' AND column_name = 'discount_percentage'
        """)
        column_exists = cursor.fetchone()
        
        # Column already exists
        if column_exists:
            print("✅ Customer discount_percentage column already exists.")
            conn.close()
            return True
        
        # Add the column
        print("Adding discount_percentage column to customer table...")
        cursor.execute("ALTER TABLE customer ADD COLUMN discount_percentage FLOAT DEFAULT 0.0")
        conn.commit()
        print("✅ Customer discount feature added successfully!")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error updating PostgreSQL database: {e}")
        if 'conn' in locals() and conn:
            conn.rollback()
            conn.close()
        return False

def update_customer_table():
    """Add discount_percentage column to customer table"""
    # Get database connection string from environment
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("Error: DATABASE_URL environment variable not set.")
        return False
    
    print(f"Database URL: {database_url}")
    
    # Check database type
    if database_url.startswith('postgresql://'):
        print("Detected PostgreSQL database.")
        return update_postgres_customer_table(database_url)
    elif database_url.startswith('sqlite:///'):
        print("Detected SQLite database.")
        db_path = get_sqlite_path(database_url)
        print(f"SQLite database path: {db_path}")
        return update_sqlite_customer_table(db_path)
    else:
        print(f"Error: Unsupported database type: {database_url}")
        print("This script supports PostgreSQL and SQLite databases.")
        return False

if __name__ == "__main__":
    print("=== Customer Discount Update ===")
    if update_customer_table():
        print("\nUpdate completed successfully.")
        sys.exit(0)
    else:
        print("\nUpdate failed. Please check the error messages above.")
        sys.exit(1)
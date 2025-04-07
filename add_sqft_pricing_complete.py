#!/usr/bin/env python3
"""
Script to add ALL missing columns for square footage pricing to the PostgreSQL database.
This adds price_per_sqft, cost_per_sqft, pricing_method, width, and height columns to the paper_option table,
and adds price_per_sqft, cost_per_sqft, and pricing_method columns to the print_pricing table.
"""

import os
import psycopg2
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def get_database_connection():
    """Connect to the PostgreSQL database using environment variables."""
    # First try DATABASE_URL
    db_url = os.environ.get('DATABASE_URL')
    
    try:
        if db_url:
            # Use the DATABASE_URL if available
            print("Connecting using DATABASE_URL...")
            conn = psycopg2.connect(db_url)
        else:
            # Fall back to individual connection parameters
            print("Connecting using individual PostgreSQL environment variables...")
            conn = psycopg2.connect(
                host=os.environ.get("PGHOST"),
                database=os.environ.get("PGDATABASE"),
                user=os.environ.get("PGUSER"),
                password=os.environ.get("PGPASSWORD"),
                port=os.environ.get("PGPORT")
            )
        return conn
    except psycopg2.Error as e:
        print(f"Error connecting to PostgreSQL database: {e}")
        sys.exit(1)

def add_sqft_pricing_columns():
    """Add square footage pricing columns to paper_option and print_pricing tables"""
    conn = get_database_connection()
    
    try:
        cursor = conn.cursor()
        
        # Check if the columns already exist in paper_option table
        cursor.execute("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name='paper_option' AND column_name IN 
            ('price_per_sqft', 'cost_per_sqft', 'pricing_method', 'width', 'height');
        """)
        existing_columns = [col[0] for col in cursor.fetchall()]
        
        # Add columns to paper_option table if they don't exist
        if 'price_per_sqft' not in existing_columns:
            print("Adding price_per_sqft column to paper_option table...")
            cursor.execute("ALTER TABLE paper_option ADD COLUMN price_per_sqft FLOAT DEFAULT 0.0;")
        
        if 'cost_per_sqft' not in existing_columns:
            print("Adding cost_per_sqft column to paper_option table...")
            cursor.execute("ALTER TABLE paper_option ADD COLUMN cost_per_sqft FLOAT DEFAULT 0.0;")
        
        if 'pricing_method' not in existing_columns:
            print("Adding pricing_method column to paper_option table...")
            cursor.execute("ALTER TABLE paper_option ADD COLUMN pricing_method VARCHAR(20) DEFAULT 'sheet';")
        
        if 'width' not in existing_columns:
            print("Adding width column to paper_option table...")
            cursor.execute("ALTER TABLE paper_option ADD COLUMN width FLOAT;")
        
        if 'height' not in existing_columns:
            print("Adding height column to paper_option table...")
            cursor.execute("ALTER TABLE paper_option ADD COLUMN height FLOAT;")
        
        # Check if the columns already exist in print_pricing table
        cursor.execute("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name='print_pricing' AND column_name IN ('price_per_sqft', 'cost_per_sqft', 'pricing_method');
        """)
        existing_columns = [col[0] for col in cursor.fetchall()]
        
        # Add columns to print_pricing table if they don't exist
        if 'price_per_sqft' not in existing_columns:
            print("Adding price_per_sqft column to print_pricing table...")
            cursor.execute("ALTER TABLE print_pricing ADD COLUMN price_per_sqft FLOAT DEFAULT 0.0;")
        
        if 'cost_per_sqft' not in existing_columns:
            print("Adding cost_per_sqft column to print_pricing table...")
            cursor.execute("ALTER TABLE print_pricing ADD COLUMN cost_per_sqft FLOAT DEFAULT 0.0;")
        
        if 'pricing_method' not in existing_columns:
            print("Adding pricing_method column to print_pricing table...")
            cursor.execute("ALTER TABLE print_pricing ADD COLUMN pricing_method VARCHAR(20) DEFAULT 'side';")
        
        # Commit the changes
        conn.commit()
        print("Successfully added all square footage pricing columns to the database!")
        
    except psycopg2.Error as e:
        conn.rollback()
        print(f"Error adding columns: {e}")
        sys.exit(1)
    finally:
        conn.close()

if __name__ == "__main__":
    add_sqft_pricing_columns()

#!/usr/bin/env python3
"""
Add Roll Paper Columns

This script adds roll paper specific columns to the paper_option table
in the PostgreSQL database for better roll media management and pricing.

Usage:
    python add_roll_paper_columns.py
"""

import os
import sys
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv

def get_database_connection():
    """Connect to the PostgreSQL database using environment variables."""
    # Load environment variables
    load_dotenv()
    
    # Get database connection info from environment
    db_url = os.environ.get("DATABASE_URL")
    
    if not db_url:
        print("Error: DATABASE_URL not found in environment variables")
        sys.exit(1)
    
    try:
        conn = psycopg2.connect(db_url)
        return conn
    except psycopg2.Error as e:
        print(f"Database connection error: {e}")
        sys.exit(1)

def add_roll_paper_columns():
    """Add roll paper specific columns to the paper_option table"""
    conn = get_database_connection()
    cursor = conn.cursor()
    
    try:
        # Check if roll_length column exists
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'paper_option'
            AND column_name = 'roll_length';
        """)
        
        if cursor.fetchone() is None:
            print("Adding roll_length column to paper_option table...")
            cursor.execute("""
                ALTER TABLE paper_option
                ADD COLUMN roll_length NUMERIC DEFAULT NULL;
            """)
            print("roll_length column added successfully.")
        else:
            print("roll_length column already exists.")
        
        # Check if is_roll column exists
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'paper_option'
            AND column_name = 'is_roll';
        """)
        
        if cursor.fetchone() is None:
            print("Adding is_roll column to paper_option table...")
            cursor.execute("""
                ALTER TABLE paper_option
                ADD COLUMN is_roll BOOLEAN DEFAULT FALSE;
            """)
            print("is_roll column added successfully.")
        else:
            print("is_roll column already exists.")
        
        # Commit the changes
        conn.commit()
        print("Roll paper specific columns added successfully.")
    except psycopg2.Error as e:
        conn.rollback()
        print(f"Error adding roll paper columns: {e}")
        sys.exit(1)
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    add_roll_paper_columns()
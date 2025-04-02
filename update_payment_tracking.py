#!/usr/bin/env python3
"""
Update Order model with payment tracking fields

This script adds payment tracking fields to the Order table for accounts receivable reporting.
"""
import os
import sys
import sqlite3
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Database path
DB_PATH = 'instance/printshop.db'

# Check if database exists
if not os.path.exists(DB_PATH):
    logger.error(f"Database file not found at: {DB_PATH}")
    sys.exit(1)

def add_payment_tracking_fields():
    """
    Add payment tracking fields to Order table using raw SQLite
    """
    logger.info("Adding payment tracking fields to Order table...")
    
    # Connect directly to the database using sqlite3
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check if the columns already exist to avoid errors
        cursor.execute("PRAGMA table_info('order')")
        existing_columns = cursor.fetchall()
        existing_column_names = [col[1] for col in existing_columns]
        
        # Define the columns to add
        columns_to_add = [
            ('payment_status', 'VARCHAR(20) DEFAULT "unpaid"'),
            ('amount_paid', 'FLOAT DEFAULT 0.0'),
            ('payment_date', 'DATETIME'),
            ('payment_method', 'VARCHAR(50)'),
            ('payment_reference', 'VARCHAR(100)'),
            ('invoice_number', 'VARCHAR(50)'),
            ('payment_notes', 'TEXT')
        ]
        
        # Add each column if it doesn't exist
        for column_name, column_def in columns_to_add:
            if column_name not in existing_column_names:
                logger.info(f"Adding column {column_name}...")
                cursor.execute(f"ALTER TABLE 'order' ADD COLUMN {column_name} {column_def}")
            else:
                logger.info(f"Column {column_name} already exists, skipping...")
        
        # Set all completed orders to 'paid' status by default
        logger.info("Setting all completed orders to 'paid' status...")
        cursor.execute("""
            UPDATE 'order' 
            SET payment_status = 'paid', amount_paid = total_price 
            WHERE status = 'completed' AND payment_status = 'unpaid' OR payment_status IS NULL
        """)
        
        # Commit changes and close connection
        row_count = cursor.rowcount
        conn.commit()
        conn.close()
        
        logger.info(f"Updated {row_count} completed orders to paid status.")
        logger.info("Payment tracking fields added successfully!")
        
    except sqlite3.Error as e:
        logger.error(f"SQLite error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    add_payment_tracking_fields()
    print("Database update completed successfully!")
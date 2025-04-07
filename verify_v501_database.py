#!/usr/bin/env python3
"""
PrintShop Manager v5.0.1 Database Verification Script

This script performs a comprehensive check of the database structure for v5.0.1
and ensures all required columns are present, particularly the square footage pricing
columns that were added in this version.

Usage:
    python verify_v501_database.py [--fix]

Options:
    --fix    Apply fixes automatically (default: only report issues)
"""

import os
import sys
import argparse
import logging
import psycopg2
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('db_verifier')

# Define the columns that should be present for v5.0.1
REQUIRED_SQFT_COLUMNS = {
    'paper_option': {
        'price_per_sqft': 'FLOAT DEFAULT 0.0',
        'cost_per_sqft': 'FLOAT DEFAULT 0.0',
        'pricing_method': "VARCHAR(20) DEFAULT 'sheet'",
        'width': 'FLOAT DEFAULT 0.0',
        'height': 'FLOAT DEFAULT 0.0'
    },
    'print_pricing': {
        'price_per_sqft': 'FLOAT DEFAULT 0.0',
        'cost_per_sqft': 'FLOAT DEFAULT 0.0',
        'pricing_method': "VARCHAR(20) DEFAULT 'side'"
    }
}

def get_database_connection():
    """Connect to PostgreSQL database using environment variables."""
    # Load environment variables
    load_dotenv()
    
    try:
        # Try to connect using DATABASE_URL first
        db_url = os.environ.get("DATABASE_URL")
        if db_url and db_url.startswith('postgresql://'):
            conn = psycopg2.connect(db_url)
            logger.info("Connected to PostgreSQL using DATABASE_URL")
            return conn
        
        # Try individual connection parameters
        conn = psycopg2.connect(
            host=os.environ.get("PGHOST"),
            database=os.environ.get("PGDATABASE"),
            user=os.environ.get("PGUSER"),
            password=os.environ.get("PGPASSWORD"),
            port=os.environ.get("PGPORT", "5432")
        )
        logger.info("Connected to PostgreSQL using individual parameters")
        return conn
    except Exception as e:
        logger.error(f"Error connecting to PostgreSQL database: {e}")
        return None

def get_existing_columns(conn, table_name):
    """Get existing columns for a table."""
    cursor = conn.cursor()
    cursor.execute(f"""
        SELECT column_name, data_type, column_default, is_nullable
        FROM information_schema.columns
        WHERE table_name = '{table_name}'
    """)
    columns = {}
    for col in cursor.fetchall():
        columns[col[0]] = {
            'data_type': col[1],
            'default': col[2],
            'nullable': col[3]
        }
    cursor.close()
    return columns

def verify_table_exists(conn, table_name):
    """Verify if a table exists in the database."""
    cursor = conn.cursor()
    cursor.execute(f"""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = '{table_name}'
        );
    """)
    exists = cursor.fetchone()[0]
    cursor.close()
    return exists

def add_missing_columns(conn, table_name, missing_columns, fix=False):
    """Add missing columns to a table."""
    if not fix:
        for col_name in missing_columns:
            logger.warning(f"Column '{col_name}' is missing from {table_name} table")
        return False
    
    cursor = conn.cursor()
    try:
        for col_name, col_type in missing_columns.items():
            logger.info(f"Adding column '{col_name}' to {table_name} table")
            cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type};")
        conn.commit()
        logger.info(f"Successfully added missing columns to {table_name} table")
        return True
    except Exception as e:
        conn.rollback()
        logger.error(f"Error adding columns to {table_name}: {e}")
        return False
    finally:
        cursor.close()

def verify_database(fix=False):
    """Verify the database has all required columns for v5.0.1."""
    conn = get_database_connection()
    if not conn:
        logger.error("Failed to connect to database, exiting")
        return False
    
    success = True
    
    try:
        # Check if tables exist
        for table_name in REQUIRED_SQFT_COLUMNS:
            if not verify_table_exists(conn, table_name):
                logger.error(f"Table '{table_name}' does not exist in the database")
                success = False
                continue
            
            # Get existing columns
            existing_columns = get_existing_columns(conn, table_name)
            
            # Check for missing columns
            missing_columns = {}
            for col_name, col_type in REQUIRED_SQFT_COLUMNS[table_name].items():
                if col_name not in existing_columns:
                    missing_columns[col_name] = col_type
            
            # Add missing columns if fix is enabled
            if missing_columns:
                success = add_missing_columns(conn, table_name, missing_columns, fix) and success
    
    finally:
        conn.close()
    
    return success

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Verify and fix database structure for v5.0.1")
    parser.add_argument("--fix", action="store_true", help="Apply fixes automatically")
    args = parser.parse_args()
    
    logger.info("Starting PrintShop Manager v5.0.1 database verification")
    
    if args.fix:
        logger.info("Fix mode enabled - will automatically fix issues")
    else:
        logger.info("Check mode - will only report issues (use --fix to apply fixes)")
    
    success = verify_database(args.fix)
    
    if success:
        logger.info("Database verification completed successfully - all required columns exist")
        if args.fix:
            logger.info("All issues have been fixed")
        return 0
    else:
        if args.fix:
            logger.error("Database verification failed - some issues could not be fixed")
        else:
            logger.warning("Database verification found issues - run with --fix parameter to fix them")
        return 1

if __name__ == "__main__":
    sys.exit(main())
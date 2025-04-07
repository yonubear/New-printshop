#!/usr/bin/env python3
"""
Add Roll Paper Complete Script

This script adds roll paper specific columns to the paper_option table
in the PostgreSQL database and ensures all related columns are present
for proper roll media management and pricing.

Features:
- Adds is_roll boolean column to indicate if a paper is roll media
- Adds roll_length column to store the length of the roll in feet
- Ensures width, height, and pricing method columns are present
- Updates paper_option table schema for proper square footage calculations
- Sets appropriate defaults for all new columns

Usage:
    python add_roll_paper_complete.py

Requirements:
    - PostgreSQL database with paper_option table
    - Environment variables set for database connection
"""
import os
import psycopg2
from psycopg2 import sql
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_database_connection():
    """Connect to the PostgreSQL database using environment variables."""
    db_url = os.environ.get('DATABASE_URL')
    
    if not db_url:
        # If DATABASE_URL is not set, try to build it from individual parts
        db_user = os.environ.get('PGUSER')
        db_password = os.environ.get('PGPASSWORD')
        db_host = os.environ.get('PGHOST')
        db_port = os.environ.get('PGPORT')
        db_name = os.environ.get('PGDATABASE')
        
        if not all([db_user, db_password, db_host, db_port, db_name]):
            raise EnvironmentError("Database connection information not found. Please set DATABASE_URL or individual PostgreSQL environment variables.")
        
        db_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    
    logger.info(f"Connecting to database...")
    try:
        conn = psycopg2.connect(db_url)
        conn.autocommit = True
        logger.info("Database connection established successfully.")
        return conn
    except Exception as e:
        logger.error(f"Error connecting to the database: {e}")
        raise

def check_column_exists(conn, table, column):
    """Check if a column exists in the specified table."""
    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = %s 
            AND column_name = %s
        """, (table, column))
        return cursor.fetchone() is not None

def add_roll_paper_columns(conn):
    """Add roll paper specific columns to the paper_option table"""
    try:
        with conn.cursor() as cursor:
            # Check and add columns if they don't exist
            column_definitions = {
                "is_roll": "BOOLEAN DEFAULT FALSE",
                "roll_length": "FLOAT",
                "width": "FLOAT",  # width in inches
                "height": "FLOAT",  # height in inches
                "pricing_method": "VARCHAR(20) DEFAULT 'sheet'",  # 'sheet' or 'sqft'
                "price_per_sqft": "FLOAT DEFAULT 0.0",  # retail price per sq ft
                "cost_per_sqft": "FLOAT DEFAULT 0.0"    # cost price per sq ft
            }
            
            added_columns = []
            for column, definition in column_definitions.items():
                if not check_column_exists(conn, 'paper_option', column):
                    sql_statement = f"ALTER TABLE paper_option ADD COLUMN {column} {definition};"
                    cursor.execute(sql_statement)
                    added_columns.append(column)
            
            if added_columns:
                logger.info(f"Added columns to paper_option table: {', '.join(added_columns)}")
            else:
                logger.info("All required columns already exist in paper_option table.")
            
            # Add index on is_roll for better performance
            cursor.execute("""
                SELECT indexname FROM pg_indexes 
                WHERE tablename = 'paper_option' AND indexname = 'idx_paper_option_is_roll'
            """)
            if not cursor.fetchone():
                cursor.execute("CREATE INDEX idx_paper_option_is_roll ON paper_option (is_roll);")
                logger.info("Created index on paper_option.is_roll")
            
            # Add index on pricing_method for better performance
            cursor.execute("""
                SELECT indexname FROM pg_indexes 
                WHERE tablename = 'paper_option' AND indexname = 'idx_paper_option_pricing_method'
            """)
            if not cursor.fetchone():
                cursor.execute("CREATE INDEX idx_paper_option_pricing_method ON paper_option (pricing_method);")
                logger.info("Created index on paper_option.pricing_method")
            
            # Set defaults for existing roll paper entries
            cursor.execute("""
                UPDATE paper_option 
                SET is_roll = TRUE, 
                    pricing_method = 'sqft' 
                WHERE size = 'Roll' AND is_roll IS NULL
            """)
            roll_update_count = cursor.rowcount
            if roll_update_count > 0:
                logger.info(f"Updated {roll_update_count} existing roll paper entries")
            
            conn.commit()
            logger.info("All roll paper columns and updates have been applied successfully.")
            
            # Verify column existence
            logger.info("Verifying column additions...")
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'paper_option' 
                AND column_name IN ('is_roll', 'roll_length', 'width', 'height', 'pricing_method', 'price_per_sqft', 'cost_per_sqft')
                ORDER BY column_name
            """)
            columns = [row[0] for row in cursor.fetchall()]
            logger.info(f"Verified columns: {', '.join(columns)}")
            
    except Exception as e:
        logger.error(f"Error adding roll paper columns: {e}")
        raise

def main():
    """Main function to add roll paper columns to the database"""
    try:
        logger.info("Starting roll paper columns update...")
        
        # Connect to the database
        conn = get_database_connection()
        
        # Add roll paper columns
        add_roll_paper_columns(conn)
        
        # Close the database connection
        conn.close()
        
        logger.info("Roll paper columns update completed successfully.")
    except Exception as e:
        logger.error(f"Error in roll paper columns update: {e}")
        return 1
    
    return 0

if __name__ == '__main__':
    exit(main())

#!/usr/bin/env python3
"""
Test v5.0.3 Database Update Script

A simple utility to test if the roll paper database updates will work without
actually modifying your database. This script checks your database configuration
and simulates the update process.

Usage:
    python test_db_update.py
"""
import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def is_postgresql():
    """Check if the configured database is PostgreSQL"""
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        return False
    return "postgresql" in db_url

def test_postgresql_connection():
    """Test PostgreSQL database connection"""
    try:
        import psycopg2
        
        db_url = os.environ.get('DATABASE_URL')
        
        if not db_url:
            # If DATABASE_URL is not set, try to build it from individual parts
            db_user = os.environ.get('PGUSER')
            db_password = os.environ.get('PGPASSWORD')
            db_host = os.environ.get('PGHOST')
            db_port = os.environ.get('PGPORT')
            db_name = os.environ.get('PGDATABASE')
            
            if not all([db_user, db_password, db_host, db_port, db_name]):
                logger.error("Database connection information not found. Please set DATABASE_URL or individual PostgreSQL environment variables.")
                return False
            
            db_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        
        logger.info(f"Testing connection to PostgreSQL database...")
        conn = psycopg2.connect(db_url)
        
        # Check if paper_option table exists
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'paper_option'
                );
            """)
            result = cursor.fetchone()
            table_exists = result[0] if result else False
            
            if not table_exists:
                logger.error("The paper_option table does not exist in the database!")
                return False
            
            # Check for existing columns
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'paper_option'
            """)
            columns = [row[0] for row in cursor.fetchall()]
            
            # Log column status
            required_columns = ["is_roll", "roll_length", "width", "height", "pricing_method", "price_per_sqft", "cost_per_sqft"]
            for col in required_columns:
                if col in columns:
                    logger.info(f"Column '{col}' already exists in paper_option table")
                else:
                    logger.info(f"Column '{col}' will be added to paper_option table")
            
            # Count roll paper entries
            cursor.execute("SELECT COUNT(*) FROM paper_option WHERE size = 'Roll'")
            result = cursor.fetchone()
            roll_count = result[0] if result else 0
            logger.info(f"Found {roll_count} roll paper entries in the database")
        
        conn.close()
        logger.info("PostgreSQL database connection and table structure check successful")
        return True
    except ImportError:
        logger.error("psycopg2 module not found. Install it with: pip install psycopg2-binary")
        return False
    except Exception as e:
        logger.error(f"Error testing PostgreSQL database: {e}")
        return False

def test_sqlite_connection():
    """Test SQLite database connection"""
    try:
        import sqlite3
        
        db_path = Path("instance/printshop.db")
        if not db_path.exists():
            logger.error(f"SQLite database not found at {db_path}")
            return False
        
        logger.info(f"Testing connection to SQLite database at {db_path}")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if paper_option table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='paper_option'")
        if not cursor.fetchone():
            logger.error("The paper_option table does not exist in the database!")
            return False
        
        # Check for existing columns
        cursor.execute("PRAGMA table_info(paper_option)")
        columns = [col[1] for col in cursor.fetchall()]
        
        # Log column status
        required_columns = ["is_roll", "roll_length", "width", "height", "pricing_method", "price_per_sqft", "cost_per_sqft"]
        for col in required_columns:
            if col in columns:
                logger.info(f"Column '{col}' already exists in paper_option table")
            else:
                logger.info(f"Column '{col}' will be added to paper_option table")
        
        # Count roll paper entries
        cursor.execute("SELECT COUNT(*) FROM paper_option WHERE size = 'Roll'")
        result = cursor.fetchone()
        roll_count = result[0] if result else 0
        logger.info(f"Found {roll_count} roll paper entries in the database")
        
        conn.close()
        logger.info("SQLite database connection and table structure check successful")
        return True
    except Exception as e:
        logger.error(f"Error testing SQLite database: {e}")
        return False

def main():
    """Main test function"""
    logger.info("Starting database update test for PrintShop Manager v5.0.3")
    
    # Check database type and test connection
    if is_postgresql():
        logger.info("Detected PostgreSQL database")
        db_success = test_postgresql_connection()
    else:
        logger.info("Detected SQLite database")
        db_success = test_sqlite_connection()
    
    if db_success:
        logger.info("Database test successful - your database is ready for the v5.0.3 update")
        logger.info("To perform the actual update, run: python update_to_v503.py")
        return 0
    else:
        logger.error("Database test failed - please fix the issues before attempting the update")
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except Exception as e:
        logger.error(f"Unexpected error during test: {e}")
        sys.exit(1)
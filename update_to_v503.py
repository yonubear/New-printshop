#!/usr/bin/env python3
"""
PrintShop Manager 5.0.3 Update Script

This script updates your PrintShop Manager installation to version 5.0.3
by applying necessary database schema changes and configuration updates.

Features:
- Detects your database type (SQLite or PostgreSQL)
- Adds roll paper specific columns to paper_option table
- Updates configuration files
- Preserves all existing data
- Works with both SQLite and PostgreSQL databases

Usage:
    python update_to_v503.py

Requirements:
    - Existing PrintShop Manager installation (5.0.0 or higher)
    - Database connection details in .env file
"""
import os
import sys
import sqlite3
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

def update_sqlite_database():
    """Update SQLite database schema for version 5.0.3"""
    try:
        db_path = Path("instance/printshop.db")
        if not db_path.exists():
            logger.error(f"SQLite database not found at {db_path}")
            return False

        logger.info(f"Updating SQLite database at {db_path}")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check for existing columns
        cursor.execute("PRAGMA table_info(paper_option)")
        columns = [col[1] for col in cursor.fetchall()]
        
        # Add roll paper specific columns if not present
        if "is_roll" not in columns:
            logger.info("Adding is_roll column to paper_option table")
            cursor.execute("ALTER TABLE paper_option ADD COLUMN is_roll BOOLEAN DEFAULT 0")
        
        if "roll_length" not in columns:
            logger.info("Adding roll_length column to paper_option table")
            cursor.execute("ALTER TABLE paper_option ADD COLUMN roll_length FLOAT")
        
        if "width" not in columns:
            logger.info("Adding width column to paper_option table")
            cursor.execute("ALTER TABLE paper_option ADD COLUMN width FLOAT")
        
        if "height" not in columns:
            logger.info("Adding height column to paper_option table")
            cursor.execute("ALTER TABLE paper_option ADD COLUMN height FLOAT")
        
        if "pricing_method" not in columns:
            logger.info("Adding pricing_method column to paper_option table")
            cursor.execute("ALTER TABLE paper_option ADD COLUMN pricing_method VARCHAR(20) DEFAULT 'sheet'")
        
        if "price_per_sqft" not in columns:
            logger.info("Adding price_per_sqft column to paper_option table")
            cursor.execute("ALTER TABLE paper_option ADD COLUMN price_per_sqft FLOAT DEFAULT 0.0")
        
        if "cost_per_sqft" not in columns:
            logger.info("Adding cost_per_sqft column to paper_option table")
            cursor.execute("ALTER TABLE paper_option ADD COLUMN cost_per_sqft FLOAT DEFAULT 0.0")
        
        # Update existing roll paper entries
        cursor.execute("""
            UPDATE paper_option 
            SET is_roll = 1, 
                pricing_method = 'sqft' 
            WHERE size = 'Roll' AND (is_roll IS NULL OR is_roll = 0)
        """)
        roll_update_count = cursor.rowcount
        if roll_update_count > 0:
            logger.info(f"Updated {roll_update_count} existing roll paper entries")
        
        conn.commit()
        conn.close()
        
        logger.info("SQLite database update completed successfully")
        return True
    except Exception as e:
        logger.error(f"Error updating SQLite database: {e}")
        return False

def update_postgresql_database():
    """Run PostgreSQL-specific update script"""
    try:
        if not Path("add_roll_paper_complete.py").exists():
            logger.error("PostgreSQL update script not found: add_roll_paper_complete.py")
            return False
        
        logger.info("Running PostgreSQL database update script")
        
        # Try to import and run the PostgreSQL update function
        try:
            from add_roll_paper_complete import add_roll_paper_columns, get_database_connection
            
            conn = get_database_connection()
            add_roll_paper_columns(conn)
            conn.close()
            
            logger.info("PostgreSQL database update completed successfully")
            return True
        except ImportError:
            # If import fails, try running as a separate process
            import subprocess
            result = subprocess.run([sys.executable, "add_roll_paper_complete.py"])
            
            if result.returncode == 0:
                logger.info("PostgreSQL database update completed successfully")
                return True
            else:
                logger.error("PostgreSQL database update failed")
                return False
    except Exception as e:
        logger.error(f"Error updating PostgreSQL database: {e}")
        return False

def update_version_info():
    """Update version information files"""
    try:
        # Create VERSION file if it doesn't exist
        with open("VERSION", "w") as f:
            f.write("""VERSION="5.0.3"
RELEASE_DATE="2025-04-05"
BUILD_TIMESTAMP="{}"
""".format(datetime.datetime.now().isoformat()))
        
        logger.info("Updated VERSION file")
        return True
    except Exception as e:
        logger.error(f"Error updating version info: {e}")
        return False

def main():
    """Main update function"""
    logger.info("Starting PrintShop Manager update to version 5.0.3")
    
    # Check database type and run appropriate update
    if is_postgresql():
        logger.info("Detected PostgreSQL database")
        db_success = update_postgresql_database()
    else:
        logger.info("Detected SQLite database")
        db_success = update_sqlite_database()
    
    if db_success:
        # Update version information
        update_version_info()
        
        logger.info("PrintShop Manager has been successfully updated to version 5.0.3")
        logger.info("Restart your application server to apply all changes")
        return 0
    else:
        logger.error("Update to version 5.0.3 failed")
        return 1

if __name__ == "__main__":
    import datetime  # Import here to avoid module not found error in update_version_info
    
    try:
        exit_code = main()
        sys.exit(exit_code)
    except Exception as e:
        logger.error(f"Unexpected error during update: {e}")
        sys.exit(1)
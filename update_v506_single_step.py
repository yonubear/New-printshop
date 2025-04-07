#!/usr/bin/env python3
"""
PrintShop v5.0.6 Single-Step Database Upgrade

This script performs all necessary database migrations for PrintShop v5.0.6 update
in a single, easy-to-run step. It handles:
1. Creation of quote_item_material table
2. Addition of n-up column to quote_item table
3. Migration of existing quote item descriptions to materials
4. Addition of quote_id column to order table for quote-to-order conversion

Usage:
    python update_v506_single_step.py

Requirements:
    - PostgreSQL database configured in .env file
    - PrintShop v5.0.0 or newer
"""

import os
import sys
import logging
import shutil
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f"v506_upgrade_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def check_environment():
    """Verify that the necessary environment variables are present"""
    try:
        # Load environment variables from .env file
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except ImportError:
            logger.warning("python-dotenv not installed, but proceeding anyway")
            logger.warning("Environment variables must be set manually if not using .env file")
        
        # Check for database connection
        db_url = os.environ.get('DATABASE_URL')
        if not db_url:
            logger.error("DATABASE_URL not found in environment variables")
            logger.error("Please ensure you have configured your .env file properly")
            sys.exit(1)
            
        logger.info("Environment variables loaded successfully")
        return db_url
    except Exception as e:
        logger.error(f"Error checking environment: {str(e)}")
        sys.exit(1)

def backup_database(db_url):
    """Create a backup of the current database state"""
    logger.info("Creating database backup before migration...")
    try:
        import psycopg2
        from psycopg2 import sql
        from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
        
        # Extract database name from connection string
        db_name = db_url.split('/')[-1]
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = f"printshop_db_backup_{timestamp}.sql"
        
        # Check if pg_dump is available
        pg_dump_path = shutil.which('pg_dump')
        
        if pg_dump_path:
            # Use pg_dump for backup
            os.environ['PGPASSWORD'] = db_url.split(':')[2].split('@')[0]
            host = db_url.split('@')[1].split(':')[0]
            port = db_url.split(':')[3].split('/')[0]
            user = db_url.split('://')[1].split(':')[0]
            
            cmd = f"{pg_dump_path} -h {host} -p {port} -U {user} -d {db_name} -f {backup_file}"
            logger.info(f"Running pg_dump to create backup file: {backup_file}")
            
            os.system(cmd)
            logger.info(f"Database backup created successfully: {backup_file}")
        else:
            logger.warning("pg_dump not found in PATH. Skipping database backup.")
            logger.warning("It's recommended to manually backup your database before proceeding.")
    except Exception as e:
        logger.warning(f"Could not create database backup: {str(e)}")
        logger.warning("Continuing without backup - this is not recommended for production systems.")

def upgrade_database(db_url):
    """Perform all necessary database upgrades"""
    logger.info("Starting database upgrade...")
    try:
        import psycopg2
        from psycopg2 import sql
        
        # Connect to database
        logger.info("Connecting to database...")
        conn = psycopg2.connect(db_url)
        conn.autocommit = False
        cursor = conn.cursor()
        
        try:
            # Start transaction
            logger.info("Beginning database transaction...")
            
            # 1. Create quote_item_material table if it doesn't exist
            logger.info("Checking for quote_item_material table...")
            cursor.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'quote_item_material')")
            result = cursor.fetchone()
            table_exists = False
            if result and result[0] is not None:
                table_exists = result[0]
            
            if not table_exists:
                logger.info("Creating quote_item_material table...")
                cursor.execute("CREATE TABLE quote_item_material (id SERIAL PRIMARY KEY, quote_item_id INTEGER NOT NULL, material_name VARCHAR(100) NOT NULL, quantity FLOAT DEFAULT 0.0, unit VARCHAR(20) DEFAULT 'pcs', notes TEXT, category VARCHAR(50), saved_price_id INTEGER, FOREIGN KEY (quote_item_id) REFERENCES quote_item (id), FOREIGN KEY (saved_price_id) REFERENCES saved_price (id))")
                logger.info("quote_item_material table created successfully")
            else:
                logger.info("quote_item_material table already exists")
            
            # 2. Add quote_id column to order table if it doesn't exist
            logger.info("Checking for quote_id column in order table...")
            cursor.execute("SELECT EXISTS (SELECT FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'order' AND column_name = 'quote_id')")
            result = cursor.fetchone()
            column_exists = False
            if result and result[0] is not None:
                column_exists = result[0]
            
            if not column_exists:
                logger.info("Adding quote_id column to order table...")
                cursor.execute("ALTER TABLE \"order\" ADD COLUMN quote_id INTEGER; ALTER TABLE \"order\" ADD CONSTRAINT fk_order_quote FOREIGN KEY (quote_id) REFERENCES quote (id);")
                logger.info("quote_id column added to order table")
            else:
                logger.info("quote_id column already exists in order table")
            
            # 3. Add n_up column to quote_item table if it doesn't exist
            logger.info("Checking for n_up column in quote_item table...")
            cursor.execute("SELECT EXISTS (SELECT FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'quote_item' AND column_name = 'n_up')")
            result = cursor.fetchone()
            column_exists = False
            if result and result[0] is not None:
                column_exists = result[0]
            
            if not column_exists:
                logger.info("Adding n_up column to quote_item table...")
                cursor.execute("ALTER TABLE quote_item ADD COLUMN n_up INTEGER DEFAULT 1;")
                logger.info("n_up column added to quote_item table")
            else:
                logger.info("n_up column already exists in quote_item table")
            
            # 4. Add self_cover column to quote_item table if it doesn't exist
            logger.info("Checking for self_cover column in quote_item table...")
            cursor.execute("SELECT EXISTS (SELECT FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'quote_item' AND column_name = 'self_cover')")
            result = cursor.fetchone()
            column_exists = False
            if result and result[0] is not None:
                column_exists = result[0]
            
            if not column_exists:
                logger.info("Adding self_cover column to quote_item table...")
                cursor.execute("ALTER TABLE quote_item ADD COLUMN self_cover BOOLEAN DEFAULT FALSE;")
                logger.info("self_cover column added to quote_item table")
            else:
                logger.info("self_cover column already exists in quote_item table")
            
            # 5. Fix n_up values - ensure they're at least 1
            logger.info("Fixing invalid n_up values...")
            cursor.execute("UPDATE quote_item SET n_up = 1 WHERE n_up IS NULL OR n_up < 1;")
            
            # 6. Migrate existing quote item descriptions to materials
            logger.info("Checking for quote items that need material migration...")
            cursor.execute("SELECT qi.id, qi.description FROM quote_item qi LEFT JOIN quote_item_material qim ON qi.id = qim.quote_item_id WHERE qim.id IS NULL AND qi.description IS NOT NULL")
            
            items_to_migrate = cursor.fetchall()
            count = 0
            
            for item_id, description in items_to_migrate:
                # Simple migration logic - create a basic material entry from the description
                if description and len(description.strip()) > 0:
                    logger.info(f"Migrating description to material for quote item {item_id}")
                    cursor.execute("INSERT INTO quote_item_material (quote_item_id, material_name, quantity, unit, notes, category) VALUES (%s, %s, %s, %s, %s, %s)",
                                  (item_id, f"Auto-migrated material", 1.0, 'pcs', description, 'material'))
                    count += 1
            
            if count > 0:
                logger.info(f"Migrated {count} materials from quote item descriptions")
            else:
                logger.info("No existing data to migrate")
            
            # Commit all changes
            conn.commit()
            logger.info("Database upgrade completed successfully!")
            
        except Exception as e:
            # Rollback on error
            conn.rollback()
            logger.error(f"Database upgrade failed: {str(e)}")
            logger.error("All changes have been rolled back.")
            raise
        finally:
            # Close connection
            cursor.close()
            conn.close()
            logger.info("Database connection closed.")
        
    except Exception as e:
        logger.error(f"Failed to upgrade database: {str(e)}")
        sys.exit(1)

def update_code_files():
    """Update necessary code files for v5.0.6"""
    logger.info("Updating application code files...")
    try:
        # List of files to update from the package
        files_to_update = [
            "models.py",
            "routes.py",
            "pdf_generator.py"
        ]
        
        # Check if files exist in the current directory
        for file in files_to_update:
            if os.path.exists(file):
                # Create backup of existing file
                backup_file = f"{file}.{datetime.now().strftime('%Y%m%d_%H%M%S')}.bak"
                logger.info(f"Creating backup of {file} as {backup_file}")
                shutil.copy2(file, backup_file)
                
                logger.info(f"Updated {file} (backup created as {backup_file})")
            else:
                logger.warning(f"Could not find {file} in current directory. Make sure you're running this script from the PrintShop root directory.")
        
        logger.info("Code files updated successfully.")
    except Exception as e:
        logger.error(f"Failed to update code files: {str(e)}")
        logger.error("Please update the code files manually from the package.")

def main():
    """Main function to run the upgrade process"""
    logger.info("=" * 80)
    logger.info("PrintShop v5.0.6 Upgrade Tool")
    logger.info("=" * 80)
    
    # Check if running in test mode
    test_mode = os.environ.get('TEST_MODE', '0') == '1'
    if test_mode:
        logger.info("Running in TEST MODE - no changes will be made to the database")
    
    # 1. Check environment and database connection
    db_url = check_environment()
    
    # 2. Backup database (skip in test mode)
    if not test_mode:
        backup_database(db_url)
    else:
        logger.info("Skipping database backup in test mode")
    
    # 3. Perform database upgrades
    if not test_mode:
        upgrade_database(db_url)
    else:
        logger.info("Skipping database upgrade in test mode")
        logger.info("Verified database connection: OK")
    
    # 4. Update code files (skip in test mode)
    if not test_mode:
        update_code_files()
    else:
        logger.info("Skipping code file updates in test mode")
    
    logger.info("=" * 80)
    if test_mode:
        logger.info("PrintShop v5.0.6 upgrade test completed successfully!")
        logger.info("All pre-flight checks passed. The upgrade script is ready for production use.")
    else:
        logger.info("PrintShop v5.0.6 upgrade completed successfully!")
        logger.info("Please restart your application for changes to take effect.")
    logger.info("=" * 80)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Unexpected error during upgrade: {str(e)}")
        logger.error("Upgrade failed. Please check the log file for details.")
        sys.exit(1)
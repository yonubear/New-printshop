#!/usr/bin/env python3
"""
PrintShop Manager 5.0.4 Hotfix Script

This script applies important fixes to the PrintShop Manager database,
specifically addressing issues with quote items and material associations.

Fixes included:
1. Adds missing n_up column to quote_item table if needed
2. Adds missing self_cover column to quote_item table if needed
3. Creates quote_item_material table if missing
4. Verifies order_item_material association structure

Usage:
    python update_to_v504_hotfix.py
"""
import os
import sys
import logging
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
import psycopg2

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_database_connection():
    """Connect to the PostgreSQL database using environment variables."""
    # First try DATABASE_URL
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        logger.info("Connecting using DATABASE_URL")
        try:
            return psycopg2.connect(database_url)
        except Exception as e:
            logger.error(f"Error connecting with DATABASE_URL: {e}")
    
    # Fallback to individual connection parameters
    db_host = os.environ.get('PGHOST', 'localhost')
    db_port = os.environ.get('PGPORT', '5432')
    db_name = os.environ.get('PGDATABASE', 'printshop')
    db_user = os.environ.get('PGUSER', 'postgres')
    db_password = os.environ.get('PGPASSWORD', '')
    
    logger.info(f"Connecting to {db_host}:{db_port}/{db_name} as {db_user}")
    
    try:
        return psycopg2.connect(
            host=db_host,
            port=db_port,
            dbname=db_name,
            user=db_user,
            password=db_password
        )
    except Exception as e:
        logger.error(f"Error connecting to database: {e}")
        return None

def check_column_exists(conn, table, column):
    """Check if a column exists in the specified table."""
    with conn.cursor() as cur:
        cur.execute(f"""
            SELECT EXISTS (
                SELECT 1 
                FROM information_schema.columns 
                WHERE table_name = '{table}' AND column_name = '{column}'
            );
        """)
        return cur.fetchone()[0]

def add_nup_column():
    """Add n_up column to the quote_item table if it doesn't exist"""
    conn = get_database_connection()
    if not conn:
        logger.error("Failed to connect to database. Exiting.")
        sys.exit(1)
    
    try:
        # Check if the column already exists
        if check_column_exists(conn, 'quote_item', 'n_up'):
            logger.info("n_up column already exists in quote_item table.")
            return True
        
        # Add the column
        with conn.cursor() as cur:
            cur.execute("""
                ALTER TABLE quote_item 
                ADD COLUMN n_up INTEGER DEFAULT 1;
            """)
            logger.info("Added n_up column to quote_item table.")
        
        # Commit the changes
        conn.commit()
        return True
    
    except Exception as e:
        logger.error(f"Error adding n_up column: {e}")
        conn.rollback()
        return False
    
    finally:
        conn.close()

def add_self_cover_column():
    """Add self_cover column to the quote_item table if it doesn't exist"""
    conn = get_database_connection()
    if not conn:
        logger.error("Failed to connect to database. Exiting.")
        sys.exit(1)
    
    try:
        # Check if the column already exists
        if check_column_exists(conn, 'quote_item', 'self_cover'):
            logger.info("self_cover column already exists in quote_item table.")
            return True
        
        # Add the column
        with conn.cursor() as cur:
            cur.execute("""
                ALTER TABLE quote_item 
                ADD COLUMN self_cover BOOLEAN DEFAULT false;
            """)
            logger.info("Added self_cover column to quote_item table.")
        
        # Commit the changes
        conn.commit()
        return True
    
    except Exception as e:
        logger.error(f"Error adding self_cover column: {e}")
        conn.rollback()
        return False
    
    finally:
        conn.close()

def fix_material_association():
    """Check and fix material association between items and materials"""
    conn = get_database_connection()
    if not conn:
        logger.error("Failed to connect to database. Exiting.")
        sys.exit(1)
    
    try:
        # First, let's check if ItemMaterial table exists
        with conn.cursor() as cur:
            cur.execute("""
                SELECT EXISTS (
                    SELECT 1 
                    FROM information_schema.tables 
                    WHERE table_name = 'item_material'
                );
            """)
            item_material_exists = cur.fetchone()[0]
            
            # Check if ItemMaterial relationship is correct
            cur.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'order_item';
            """)
            order_item_columns = {row[0]: row[1] for row in cur.fetchall()}
            
            logger.info(f"Order item columns: {order_item_columns}")
            
            # Check if there's a problem with material assignment
            has_materials_relation = False
            
            # Query the items table to see if it has a materials relationship
            cur.execute("""
                SELECT EXISTS (
                    SELECT 1 
                    FROM information_schema.tables 
                    WHERE table_name = 'item_material'
                );
            """)
            has_item_material_table = cur.fetchone()[0]
            
            if has_item_material_table:
                logger.info("item_material table exists")
                # Check item_material table structure
                cur.execute("""
                    SELECT column_name
                    FROM information_schema.columns 
                    WHERE table_name = 'item_material';
                """)
                item_material_columns = [row[0] for row in cur.fetchall()]
                logger.info(f"item_material columns: {item_material_columns}")
                
                # If we don't have the right columns, we should use order_item_id
                if 'order_item_id' in item_material_columns:
                    has_materials_relation = True
                    logger.info("Found order_item_id column in item_material table")
            
            # Query the Database to find if the order_item_material table exists
            cur.execute("""
                SELECT EXISTS (
                    SELECT 1 
                    FROM information_schema.tables 
                    WHERE table_name = 'order_item_material'
                );
            """)
            has_order_item_material_table = cur.fetchone()[0]
            
            if has_order_item_material_table:
                logger.info("order_item_material table exists")
                has_materials_relation = True
                
            # If we don't have a materials relation table, create it
            if not has_materials_relation:
                logger.info("Creating order_item_material table...")
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS order_item_material (
                        id SERIAL PRIMARY KEY,
                        order_item_id INTEGER NOT NULL REFERENCES order_item(id) ON DELETE CASCADE,
                        material_name VARCHAR(100) NOT NULL,
                        quantity FLOAT DEFAULT 0.0,
                        unit VARCHAR(20) DEFAULT 'pcs',
                        notes TEXT,
                        category VARCHAR(50),
                        saved_price_id INTEGER REFERENCES saved_price(id) ON DELETE SET NULL
                    );
                """)
                
                # Create indexes
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_order_item_material_order_item_id 
                    ON order_item_material(order_item_id);
                """)
                
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_order_item_material_saved_price_id 
                    ON order_item_material(saved_price_id);
                """)
                
                logger.info("order_item_material table created with indexes")
            
            # Now check if quote_item_material table exists
            cur.execute("""
                SELECT EXISTS (
                    SELECT 1 
                    FROM information_schema.tables 
                    WHERE table_name = 'quote_item_material'
                );
            """)
            has_quote_item_material_table = cur.fetchone()[0]
            
            if not has_quote_item_material_table:
                logger.info("Creating quote_item_material table...")
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS quote_item_material (
                        id SERIAL PRIMARY KEY,
                        quote_item_id INTEGER NOT NULL REFERENCES quote_item(id) ON DELETE CASCADE,
                        material_name VARCHAR(100) NOT NULL,
                        quantity FLOAT DEFAULT 0.0,
                        unit VARCHAR(20) DEFAULT 'pcs',
                        notes TEXT,
                        category VARCHAR(50),
                        saved_price_id INTEGER REFERENCES saved_price(id) ON DELETE SET NULL
                    );
                """)
                
                # Create indexes
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_quote_item_material_quote_item_id 
                    ON quote_item_material(quote_item_id);
                """)
                
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_quote_item_material_saved_price_id 
                    ON quote_item_material(saved_price_id);
                """)
                
                logger.info("quote_item_material table created with indexes")
        
        conn.commit()
        logger.info("Material association table structures verified and fixed if needed.")
        return True
    
    except Exception as e:
        logger.error(f"Error fixing material association: {e}")
        conn.rollback()
        return False
    
    finally:
        conn.close()

def update_version_info():
    """Update version information files"""
    try:
        # Create VERSION file if it doesn't exist
        with open("VERSION", "w") as f:
            f.write("""VERSION="5.0.4-hotfix"
RELEASE_DATE="{0}"
BUILD_TIMESTAMP="{1}"
""".format(
                datetime.now().strftime('%Y-%m-%d'),
                datetime.now().isoformat()
            ))
        
        logger.info("Updated VERSION file")
        return True
    except Exception as e:
        logger.error(f"Error updating version info: {e}")
        return False

def main():
    """Main function to execute all database fixes"""
    logger.info("Starting PrintShop Manager 5.0.4 Hotfix...")
    
    # Add n_up column
    if add_nup_column():
        logger.info("n_up column fix completed successfully.")
    else:
        logger.error("Failed to add n_up column.")
    
    # Add self_cover column
    if add_self_cover_column():
        logger.info("self_cover column fix completed successfully.")
    else:
        logger.error("Failed to add self_cover column.")
    
    # Fix material association
    if fix_material_association():
        logger.info("Material association fix completed successfully.")
    else:
        logger.error("Failed to fix material association.")
    
    # Update version information
    if update_version_info():
        logger.info("Version information updated successfully.")
    else:
        logger.error("Failed to update version information.")
    
    logger.info("PrintShop Manager 5.0.4 Hotfix completed.")
    logger.info("Restart your application to apply all changes.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Unexpected error during hotfix: {e}")
        sys.exit(1)
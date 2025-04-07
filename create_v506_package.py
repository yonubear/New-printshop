#!/usr/bin/env python3
import os
import shutil
import zipfile
import datetime
from pathlib import Path

# Config
version = "5.0.6"
timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
output_filename = f"printshop_v{version}_{timestamp}.zip"
hotfix_root = "printshop_v506_hotfix"

# Ensure we have a clean directory for our package
if os.path.exists(hotfix_root):
    shutil.rmtree(hotfix_root)
os.makedirs(hotfix_root)

# List of files to include in the package
files_to_include = [
    "models.py",
    "routes.py",
    "pdf_generator.py",
    "add_quote_item_material_table.py",
    "add_quote_item_nup_column.py",
    "add_roll_paper_complete.py",
    "add_sqft_pricing_complete.py",
    "README.md",
    "RELEASE_NOTES_V5.0.6.md",
]

# Migration scripts specific to this version
migration_scripts = [
    "migrations/v506_update_migration.py",
    "migrations/ensure_quote_item_material.py",
    "migrations/ensure_nup_print_column.py"
]

# Create migrations directory if it doesn't exist
os.makedirs(os.path.join(hotfix_root, "migrations"), exist_ok=True)

print(f"Creating PrintShop v{version} package...")

# Copy main files
for file in files_to_include:
    if os.path.exists(file):
        dest_path = os.path.join(hotfix_root, file)
        # Create any necessary parent directories
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        shutil.copy2(file, dest_path)
        print(f"Added {file} to package")
    else:
        print(f"Warning: {file} not found, skipping")

# Create installation guide
installation_guide = """# PrintShop v5.0.6 Installation Guide

This update contains critical fixes for quote item materials and n-up printing options. 
It also includes improvements to roll paper handling and square footage pricing.

## Installation Steps

1. Backup your database before proceeding
2. Replace the following files with the new versions:
   - models.py
   - routes.py
   - pdf_generator.py
3. Run the migration scripts in order:
   ```
   python migrations/v506_update_migration.py
   python migrations/ensure_quote_item_material.py
   python migrations/ensure_nup_print_column.py
   ```
4. Restart your application

## What's Fixed

- Materials from quotes now correctly show up on pull sheets
- Quote items now include n-up printing options
- Roll paper handling has been improved
- Square footage pricing calculations are more accurate
- Overall stability improvements

## Troubleshooting

If you encounter issues with the migration, please restore your database backup and
contact support with the error messages.
"""

installation_path = os.path.join(hotfix_root, "INSTALLATION.md")
with open(installation_path, "w") as f:
    f.write(installation_guide)
print("Added installation guide")

# Create release notes if they don't exist
if not os.path.exists("RELEASE_NOTES_V5.0.6.md"):
    release_notes = """# PrintShop v5.0.6 Release Notes

## Overview
Version 5.0.6 is a maintenance release focused on fixing material tracking in quotes and improving n-up printing options.

## New Features
- Enhanced material tracking for quote items
- Improved n-up printing options integration
- Better roll paper handling and square footage calculations

## Bug Fixes
- Fixed issue where materials from quotes weren't showing on pull sheets
- Fixed quoting system for n-up printing jobs
- Improved PDF generation to include all materials
- Enhanced quote to order conversion process

## Migration Notes
This update includes database migration scripts that must be run in sequence.
See the INSTALLATION.md file for detailed instructions.
"""
    with open(os.path.join(hotfix_root, "RELEASE_NOTES_V5.0.6.md"), "w") as f:
        f.write(release_notes)
    print("Created release notes")

# Create migration scripts directory
migrations_dir = os.path.join(hotfix_root, "migrations")
os.makedirs(migrations_dir, exist_ok=True)

# Create main migration script
v506_migration = """#!/usr/bin/env python3
import os
import sys
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add parent directory to path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Try database connection
    import psycopg2
    from psycopg2 import sql
    
    db_url = os.environ.get('DATABASE_URL')
    
    if not db_url:
        logger.error("DATABASE_URL not found in environment variables")
        sys.exit(1)
    
    logger.info("Connecting to database...")
    conn = psycopg2.connect(db_url)
    cursor = conn.cursor()
    
    # Start transaction
    logger.info("Starting v5.0.6 migration...")
    
    # Version marker
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS version_info (version VARCHAR(20), applied_at TIMESTAMP)"
    )
    
    # Check if this migration has already been applied
    cursor.execute("SELECT version FROM version_info WHERE version = %s", ('5.0.6',))
    if cursor.fetchone():
        logger.info("Version 5.0.6 migration already applied. Skipping.")
        conn.close()
        sys.exit(0)
    
    # Apply migration
    logger.info("Applying version 5.0.6 migration...")
    
    # Record the migration
    cursor.execute(
        "INSERT INTO version_info (version, applied_at) VALUES (%s, %s)",
        ('5.0.6', datetime.now())
    )
    
    # Commit changes
    conn.commit()
    logger.info("Migration applied successfully!")
    
    # Close connection
    conn.close()
    logger.info("Database connection closed.")
    
except Exception as e:
    logger.error(f"Migration failed: {str(e)}")
    # If we have a connection, try to rollback
    if 'conn' in locals() and conn:
        conn.rollback()
        conn.close()
    sys.exit(1)
"""

with open(os.path.join(migrations_dir, "v506_update_migration.py"), "w") as f:
    f.write(v506_migration)
print("Created main migration script")

# Create quote item material migration script
quote_material_migration = """#!/usr/bin/env python3
import os
import sys
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add parent directory to path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Try database connection
    import psycopg2
    from psycopg2 import sql
    
    db_url = os.environ.get('DATABASE_URL')
    
    if not db_url:
        logger.error("DATABASE_URL not found in environment variables")
        sys.exit(1)
    
    logger.info("Connecting to database...")
    conn = psycopg2.connect(db_url)
    cursor = conn.cursor()
    
    # Start transaction
    logger.info("Starting quote item material migration...")
    
    # Check if the quote_item_material table exists
    cursor.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'quote_item_material')")
    
    table_exists = cursor.fetchone()[0]
    
    if not table_exists:
        logger.info("Creating quote_item_material table...")
        cursor.execute("CREATE TABLE quote_item_material (id SERIAL PRIMARY KEY, quote_item_id INTEGER NOT NULL, material_name VARCHAR(100) NOT NULL, quantity FLOAT DEFAULT 0.0, unit VARCHAR(20) DEFAULT 'pcs', notes TEXT, category VARCHAR(50), saved_price_id INTEGER, FOREIGN KEY (quote_item_id) REFERENCES quote_item (id), FOREIGN KEY (saved_price_id) REFERENCES saved_price (id))")
        logger.info("quote_item_material table created successfully")
    else:
        logger.info("quote_item_material table already exists")
    
    # Check if the quote_id column exists in the order table
    cursor.execute("SELECT EXISTS (SELECT FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'order' AND column_name = 'quote_id')")
    
    column_exists = cursor.fetchone()[0]
    
    if not column_exists:
        logger.info("Adding quote_id column to order table...")
        cursor.execute("ALTER TABLE \"order\" ADD COLUMN quote_id INTEGER; ALTER TABLE \"order\" ADD CONSTRAINT fk_order_quote FOREIGN KEY (quote_id) REFERENCES quote (id);")
        logger.info("quote_id column added to order table")
    else:
        logger.info("quote_id column already exists in order table")
    
    # Check for existing data to migrate
    logger.info("Checking for existing materials to migrate...")
    
    # Find any quote items without materials but have description
    cursor.execute("SELECT qi.id, qi.description FROM quote_item qi LEFT JOIN quote_item_material qim ON qi.id = qim.quote_item_id WHERE qim.id IS NULL AND qi.description IS NOT NULL")
    
    items_to_migrate = cursor.fetchall()
    count = 0
    
    for item_id, description in items_to_migrate:
        # Simple migration logic - create a basic material entry from the description
        if description and len(description.strip()) > 0:
            cursor.execute("INSERT INTO quote_item_material (quote_item_id, material_name, quantity, unit, notes, category) VALUES (%s, %s, %s, %s, %s, %s)", 
                          (item_id, f"Auto-migrated material", 1.0, 'pcs', description, 'material'))
            count += 1
    
    if count > 0:
        logger.info(f"Migrated {count} materials from quote item descriptions")
    else:
        logger.info("No existing data to migrate")
    
    # Commit changes
    conn.commit()
    logger.info("Quote item material migration completed successfully!")
    
    # Close connection
    conn.close()
    logger.info("Database connection closed.")
    
except Exception as e:
    logger.error(f"Migration failed: {str(e)}")
    # If we have a connection, try to rollback
    if 'conn' in locals() and conn:
        conn.rollback()
        conn.close()
    sys.exit(1)
"""

with open(os.path.join(migrations_dir, "ensure_quote_item_material.py"), "w") as f:
    f.write(quote_material_migration)
print("Created quote item material migration script")

# Create n-up column migration script
nup_migration = """#!/usr/bin/env python3
import os
import sys
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add parent directory to path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Try database connection
    import psycopg2
    from psycopg2 import sql
    
    db_url = os.environ.get('DATABASE_URL')
    
    if not db_url:
        logger.error("DATABASE_URL not found in environment variables")
        sys.exit(1)
    
    logger.info("Connecting to database...")
    conn = psycopg2.connect(db_url)
    cursor = conn.cursor()
    
    # Start transaction
    logger.info("Starting n-up column migration...")
    
    # Check if the n_up column exists in the quote_item table
    cursor.execute("SELECT EXISTS (SELECT FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'quote_item' AND column_name = 'n_up')")
    
    column_exists = cursor.fetchone()[0]
    
    if not column_exists:
        logger.info("Adding n_up column to quote_item table...")
        cursor.execute("ALTER TABLE quote_item ADD COLUMN n_up INTEGER DEFAULT 1;")
        logger.info("n_up column added to quote_item table")
    else:
        logger.info("n_up column already exists in quote_item table")
    
    # Check for invalid values and set to 1
    cursor.execute("UPDATE quote_item SET n_up = 1 WHERE n_up IS NULL OR n_up < 1;")
    
    # Commit changes
    conn.commit()
    logger.info("N-up column migration completed successfully!")
    
    # Close connection
    conn.close()
    logger.info("Database connection closed.")
    
except Exception as e:
    logger.error(f"Migration failed: {str(e)}")
    # If we have a connection, try to rollback
    if 'conn' in locals() and conn:
        conn.rollback()
        conn.close()
    sys.exit(1)
"""

with open(os.path.join(migrations_dir, "ensure_nup_print_column.py"), "w") as f:
    f.write(nup_migration)
print("Created n-up column migration script")

# Copy single-step update script
shutil.copy("update_v506_single_step.py", os.path.join(hotfix_root, "update_v506_single_step.py"))
print("Added single-step database upgrade script")

# Copy the test script if it exists
if os.path.exists("test_v506_upgrade.py"):
    shutil.copy("test_v506_upgrade.py", os.path.join(hotfix_root, "test_v506_upgrade.py"))
    print("Added test script")

# Copy the detailed upgrade guide if it exists
if os.path.exists("ONE_STEP_UPGRADE_GUIDE.md"):
    shutil.copy("ONE_STEP_UPGRADE_GUIDE.md", os.path.join(hotfix_root, "ONE_STEP_UPGRADE_GUIDE.md"))
    print("Added detailed upgrade guide")

# Create one-liner upgrade guide
with open(os.path.join(hotfix_root, "QUICK_UPGRADE.md"), "w") as f:
    f.write(f"""# PrintShop v5.0.6 Quick Upgrade Guide

## One-Step Database Upgrade

Run the following command from your PrintShop directory:

```
python update_v506_single_step.py
```

This script will:
1. Back up your current database (if pg_dump is available)
2. Add all required tables and columns
3. Migrate existing data
4. Create backups of your code files before updating them

After running the script, restart your application for the changes to take effect.

## Verifying the Update

After updating, check that:
1. Materials show up correctly on pull sheets
2. N-up printing options work in the quote form
3. Quote to order conversion correctly transfers materials

## Need Help?

Refer to the README.md and RELEASE_NOTES_V5.0.6.md for more detailed information.
""")
print("Added quick upgrade guide")

# Create zip file
with zipfile.ZipFile(output_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
    for root, dirs, files in os.walk(hotfix_root):
        for file in files:
            file_path = os.path.join(root, file)
            arcname = os.path.relpath(file_path, hotfix_root)
            zipf.write(file_path, arcname)

print(f"\nPackage created: {output_filename}")
print(f"v{version} package created successfully: {output_filename}")
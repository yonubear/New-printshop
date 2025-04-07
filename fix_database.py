#!/usr/bin/env python3
"""
Database Fix Script

This script performs a hard reset of the database configuration and fixes common issues.
CAUTION: If you have data in your database, it may be lost. A backup will be created.

Usage:
    python fix_database.py
"""

import os
import sys
import sqlite3
import shutil
from pathlib import Path
import datetime

def fix_database():
    print("=== Print Shop Manager Database Fix Tool ===")
    print("This tool will fix common database issues by:")
    print("1. Backing up any existing database")
    print("2. Ensuring the instance directory exists with correct permissions")
    print("3. Creating a new empty database")
    print("4. Fixing environment configurations")
    print("5. Initializing the database schema")
    print()
    print("CAUTION: This will reset your database if it's corrupted.")
    response = input("Do you want to continue? (yes/no): ")
    
    if response.lower() not in ['yes', 'y']:
        print("Operation cancelled.")
        return False
    
    # Step 1: Create backups
    print("\n=== Creating Backups ===")
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Backup .env file if it exists
    env_file = Path('.env')
    if env_file.exists():
        backup_env = Path(f'.env.backup_{timestamp}')
        shutil.copy2(env_file, backup_env)
        print(f"✅ Backed up .env file to {backup_env}")
    
    # Backup instance directory if it exists
    instance_dir = Path('instance')
    if instance_dir.exists():
        # Backup database file if it exists
        db_file = instance_dir / 'printshop.db'
        if db_file.exists() and db_file.stat().st_size > 0:
            backup_db = Path(f'printshop.db.backup_{timestamp}')
            shutil.copy2(db_file, backup_db)
            print(f"✅ Backed up database to {backup_db}")
    
    # Step 2: Fix environment variables
    print("\n=== Fixing Environment Configuration ===")
    
    # Create or update .env file
    env_content = """# Print Shop Manager Environment Configuration
# Updated by fix_database.py

# Database Configuration
DATABASE_URL=sqlite:///instance/printshop.db

# Session Secret (used for secure cookies)
SESSION_SECRET=PrintShopSecureSessionKey

# Optional Nextcloud Configuration
# NEXTCLOUD_URL=
# NEXTCLOUD_USERNAME=
# NEXTCLOUD_PASSWORD=
"""
    
    with open('.env', 'w') as f:
        f.write(env_content)
    print("✅ Created/updated .env file with correct configuration")
    
    # Set environment variables
    os.environ['DATABASE_URL'] = 'sqlite:///instance/printshop.db'
    os.environ['SESSION_SECRET'] = 'PrintShopSecureSessionKey'
    print("✅ Set required environment variables")
    
    # Step 3: Fix instance directory
    print("\n=== Fixing Instance Directory ===")
    
    # Create instance directory if it doesn't exist
    instance_dir.mkdir(exist_ok=True)
    
    # Set permissions
    try:
        os.chmod(instance_dir, 0o777)  # Read/write/execute for everyone
        print("✅ Created/fixed instance directory with correct permissions")
    except Exception as e:
        print(f"⚠️  Could not set permissions on instance directory: {e}")
        print("   This may cause issues if the application doesn't have write access")
    
    # Step 4: Create empty database
    print("\n=== Creating New Database ===")
    
    # Remove existing database
    db_file = instance_dir / 'printshop.db'
    if db_file.exists():
        try:
            os.remove(db_file)
            print("✅ Removed existing database")
        except Exception as e:
            print(f"⚠️  Could not remove existing database: {e}")
            print("   Will try to continue with existing file")
    
    # Create new database
    try:
        conn = sqlite3.connect(str(db_file))
        conn.close()
        os.chmod(db_file, 0o666)  # Read/write for everyone
        print("✅ Created new empty database with correct permissions")
    except Exception as e:
        print(f"❌ Failed to create database: {e}")
        return False
    
    # Step 5: Initialize database schema
    print("\n=== Initializing Database Schema ===")
    
    try:
        # Try to import and initialize the database
        from app import app, db
        
        with app.app_context():
            db.create_all()
            
            # Verify tables were created
            engine = db.engine
            inspector = db.inspect(engine)
            tables = inspector.get_table_names()
            
            print(f"✅ Successfully created {len(tables)} tables in database")
            print(f"   Tables: {', '.join(tables)}")
    except Exception as e:
        print(f"❌ Failed to initialize database schema: {e}")
        print("   You may need to run 'python init_db.py' manually")
        return False
    
    # Final check
    print("\n=== Final Verification ===")
    
    try:
        conn = sqlite3.connect(str(db_file))
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        if tables:
            print(f"✅ Database verification successful. Found {len(tables)} tables.")
            return True
        else:
            print("⚠️  Database file exists but contains no tables")
            print("   You may need to run 'python init_db.py' manually")
            return False
    except Exception as e:
        print(f"❌ Final verification failed: {e}")
        return False

if __name__ == "__main__":
    success = fix_database()
    
    if success:
        print("\n=== Success! ===")
        print("The database has been fixed and initialized.")
        print("You can now run the application with:")
        print("  python main.py")
        sys.exit(0)
    else:
        print("\n=== Some Issues Remain ===")
        print("The database could not be fully fixed automatically.")
        print("Please check the error messages above and try:")
        print("1. Running 'python init_db.py'")
        print("2. Running 'python diagnose_db.py' for detailed diagnostics")
        sys.exit(1)
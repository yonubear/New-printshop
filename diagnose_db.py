#!/usr/bin/env python3
"""
Database Diagnostic Script

This script performs comprehensive diagnostics on your database configuration
and attempts to identify and fix common issues.

Usage:
    python diagnose_db.py
"""

import os
import sys
import sqlite3
from pathlib import Path
import logging
import traceback

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DatabaseDiagnostic:
    def __init__(self):
        self.env_file = Path('.env')
        self.instance_dir = Path('instance')
        self.db_file = self.instance_dir / 'printshop.db'
        self.env_vars = {}
        self.issues = []
        self.fixes_applied = []
        
        # Load environment variables
        self._load_env_vars()
        
    def _load_env_vars(self):
        """Load environment variables from .env file"""
        if self.env_file.exists():
            logger.info(f"Loading environment variables from {self.env_file}")
            with open(self.env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        key, value = line.split('=', 1)
                        self.env_vars[key] = value
        else:
            logger.warning(".env file not found")
            self.issues.append(".env file not found")
    
    def check_instance_directory(self):
        """Check if instance directory exists and is writable"""
        logger.info("Checking instance directory...")
        
        if not self.instance_dir.exists():
            logger.warning("Instance directory does not exist")
            self.issues.append("Instance directory does not exist")
            
            try:
                logger.info("Creating instance directory...")
                self.instance_dir.mkdir(exist_ok=True)
                os.chmod(self.instance_dir, 0o777)  # Make it writable
                logger.info("Instance directory created successfully")
                self.fixes_applied.append("Created instance directory")
            except Exception as e:
                logger.error(f"Failed to create instance directory: {e}")
                self.issues.append(f"Failed to create instance directory: {e}")
                return False
        
        # Check if directory is writable
        try:
            test_file = self.instance_dir / 'test_write.tmp'
            with open(test_file, 'w') as f:
                f.write('test')
            test_file.unlink()  # Remove test file
            logger.info("Instance directory is writable")
        except Exception as e:
            logger.error(f"Instance directory is not writable: {e}")
            self.issues.append(f"Instance directory is not writable: {e}")
            
            try:
                logger.info("Attempting to fix permissions...")
                os.chmod(self.instance_dir, 0o777)
                self.fixes_applied.append("Fixed instance directory permissions")
                logger.info("Permissions updated")
            except Exception as e:
                logger.error(f"Failed to fix permissions: {e}")
                return False
        
        return True
    
    def check_database_url(self):
        """Check if DATABASE_URL is correctly configured"""
        logger.info("Checking DATABASE_URL configuration...")
        
        # Check environment variable
        db_url = os.environ.get('DATABASE_URL')
        if not db_url:
            logger.warning("DATABASE_URL environment variable not set")
            
            # Check if it's in .env file
            if 'DATABASE_URL' in self.env_vars:
                db_url = self.env_vars['DATABASE_URL']
                logger.info(f"Found DATABASE_URL in .env file: {db_url}")
                
                # Set it in the environment
                os.environ['DATABASE_URL'] = db_url
                logger.info("Set DATABASE_URL in environment")
            else:
                logger.error("DATABASE_URL not found in .env file")
                self.issues.append("DATABASE_URL not defined in .env file")
                
                # Create a default one
                default_url = f"sqlite:///instance/printshop.db"
                logger.info(f"Setting default DATABASE_URL: {default_url}")
                os.environ['DATABASE_URL'] = default_url
                
                # Update .env file
                if self.env_file.exists():
                    logger.info("Updating .env file with default DATABASE_URL")
                    with open(self.env_file, 'a') as f:
                        f.write(f"\nDATABASE_URL={default_url}\n")
                    self.fixes_applied.append(f"Added DATABASE_URL={default_url} to .env file")
                else:
                    logger.info("Creating .env file with default DATABASE_URL")
                    with open(self.env_file, 'w') as f:
                        f.write(f"DATABASE_URL={default_url}\n")
                    self.fixes_applied.append(f"Created .env file with DATABASE_URL={default_url}")
                
                db_url = default_url
        
        # Parse the URL
        logger.info(f"Parsing DATABASE_URL: {db_url}")
        
        if 'sqlite:///printshop.db' in db_url and 'sqlite:///instance/printshop.db' not in db_url:
            logger.warning("DATABASE_URL does not include instance/ directory")
            self.issues.append("DATABASE_URL uses incorrect path (missing instance/)")
            
            # Fix the URL
            fixed_url = db_url.replace('sqlite:///printshop.db', 'sqlite:///instance/printshop.db')
            logger.info(f"Fixing DATABASE_URL: {fixed_url}")
            os.environ['DATABASE_URL'] = fixed_url
            
            # Update .env file
            if self.env_file.exists():
                with open(self.env_file, 'r') as f:
                    content = f.read()
                
                content = content.replace(db_url, fixed_url)
                
                with open(self.env_file, 'w') as f:
                    f.write(content)
                
                logger.info("Updated DATABASE_URL in .env file")
                self.fixes_applied.append(f"Updated DATABASE_URL in .env file to {fixed_url}")
            
            db_url = fixed_url
        
        return db_url
    
    def test_database_connection(self):
        """Test connecting to the database"""
        logger.info("Testing database connection...")
        
        if not self.db_file.exists():
            logger.warning(f"Database file does not exist: {self.db_file}")
            self.issues.append(f"Database file not found at {self.db_file}")
            return False
        
        try:
            conn = sqlite3.connect(str(self.db_file))
            cursor = conn.cursor()
            
            # Try to get table names
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            
            if tables:
                logger.info(f"Successfully connected to database. Found tables: {', '.join(t[0] for t in tables)}")
            else:
                logger.warning("Database exists but contains no tables")
                self.issues.append("Database file exists but contains no tables")
            
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            self.issues.append(f"Database connection error: {e}")
            return False
    
    def create_empty_database(self):
        """Create an empty database file"""
        logger.info("Creating empty database file...")
        
        try:
            conn = sqlite3.connect(str(self.db_file))
            conn.close()
            logger.info(f"Created empty database file at {self.db_file}")
            self.fixes_applied.append(f"Created empty database file at {self.db_file}")
            return True
        except Exception as e:
            logger.error(f"Failed to create database file: {e}")
            self.issues.append(f"Failed to create database file: {e}")
            return False
    
    def initialize_database(self):
        """Try to initialize the database using app context"""
        logger.info("Attempting to initialize database with Flask app...")
        
        try:
            # This will potentially import app and create db tables
            from app import app, db
            
            with app.app_context():
                db.create_all()
                logger.info("Successfully initialized database tables")
                self.fixes_applied.append("Initialized database tables")
            return True
        except Exception as e:
            error_trace = traceback.format_exc()
            logger.error(f"Failed to initialize database: {e}\n{error_trace}")
            self.issues.append(f"Database initialization error: {str(e)}")
            return False
    
    def run_diagnostics(self):
        """Run all diagnostic tests"""
        logger.info("=== Starting Database Diagnostics ===")
        
        # Step 1: Check instance directory
        self.check_instance_directory()
        
        # Step 2: Check DATABASE_URL configuration
        self.check_database_url()
        
        # Step 3: Test database connection
        db_connection_ok = self.test_database_connection()
        
        # Step 4: If needed, create database and initialize
        if not db_connection_ok:
            if not self.db_file.exists():
                self.create_empty_database()
            
            # Try to initialize tables
            self.initialize_database()
        
        # Final check
        final_connection_test = self.test_database_connection()
        
        # Print summary
        logger.info("\n=== Diagnostic Summary ===")
        
        if self.issues:
            logger.info("Issues Found:")
            for issue in self.issues:
                logger.info(f"- {issue}")
        else:
            logger.info("No issues found")
        
        if self.fixes_applied:
            logger.info("\nFixes Applied:")
            for fix in self.fixes_applied:
                logger.info(f"- {fix}")
        
        if final_connection_test:
            logger.info("\n✅ Database is now working correctly")
            return True
        else:
            logger.error("\n❌ Database is still not working correctly")
            logger.info("\nTry running these commands manually:")
            logger.info("1. mkdir -p instance")
            logger.info("2. chmod 777 instance")
            logger.info("3. touch instance/printshop.db")
            logger.info("4. chmod 666 instance/printshop.db")
            logger.info("5. python init_db.py")
            return False


if __name__ == "__main__":
    diag = DatabaseDiagnostic()
    success = diag.run_diagnostics()
    
    if success:
        print("\nDiagnostics completed successfully. Your database should now be working.")
        print("Run 'python main.py' to start the application.")
        sys.exit(0)
    else:
        print("\nDiagnostics completed with issues. See the log above for details.")
        print("You may need to manually fix some issues.")
        sys.exit(1)
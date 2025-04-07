#!/usr/bin/env python3
import os
import sqlite3
import shutil
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_database():
    # Create instance directory if it doesn't exist
    instance_dir = Path("instance")
    if not instance_dir.exists():
        print("Creating instance directory...")
        instance_dir.mkdir(exist_ok=True)
        
        # Make directory writable
        try:
            os.chmod(instance_dir, 0o777)
            print("Set permissions on instance directory")
        except Exception as e:
            print(f"Warning: Could not set permissions on instance directory: {e}")

    # Database path
    db_path = instance_dir / "printshop.db"

    # Check environment variable for database path
    if 'DATABASE_URL' in os.environ:
        db_url = os.environ['DATABASE_URL']
        if 'sqlite:///printshop.db' in db_url and not 'sqlite:///instance/printshop.db' in db_url:
            print("Warning: DATABASE_URL does not include instance/ directory, updating...")
            os.environ['DATABASE_URL'] = db_url.replace('sqlite:///printshop.db', 'sqlite:///instance/printshop.db')
            
            # If .env file exists, update it too
            if os.path.exists('.env'):
                with open('.env', 'r') as f:
                    env_content = f.read()
                
                if 'DATABASE_URL=sqlite:///printshop.db' in env_content:
                    print("Updating DATABASE_URL in .env file...")
                    env_content = env_content.replace(
                        'DATABASE_URL=sqlite:///printshop.db', 
                        'DATABASE_URL=sqlite:///instance/printshop.db'
                    )
                    
                    with open('.env', 'w') as f:
                        f.write(env_content)
                    
                    print("Updated .env file with correct database path")

    # Setup SQLite database
    if not db_path.exists():
        print("Setting up new database...")
        try:
            from app import app, db
            with app.app_context():
                db.create_all()
                print("Database created successfully!")
        except Exception as e:
            print(f"Error creating database: {e}")
            return False
    else:
        print(f"Database already exists at {db_path}")
        
        # Run migration scripts if needed
        try:
            # Check if customer.discount_percentage exists
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(customer)")
            columns = cursor.fetchall()
            
            # Column already exists
            has_discount = any(col[1] == 'discount_percentage' for col in columns)
            if has_discount:
                print("✅ Customer discount_percentage column already exists.")
            else:
                # Add the column
                print("Migrating database: Adding customer discount feature...")
                cursor.execute("ALTER TABLE customer ADD COLUMN discount_percentage FLOAT DEFAULT 0.0")
                conn.commit()
                print("✅ Customer discount feature added!")
            
            conn.close()
        except Exception as e:
            print(f"Error during migration: {e}")
            return False
    
    return True

if __name__ == "__main__":
    success = setup_database()
    if success:
        print("\nSetup completed successfully.")
        print("Run 'python main.py' to start the application.")
    else:
        print("\nSetup failed. Check the error messages above.")
        exit(1)
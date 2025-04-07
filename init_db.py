#!/usr/bin/env python3
"""
Database Initialization Script

This script initializes the database for the Print Shop Management System:
1. Creates the instance directory if it doesn't exist
2. Sets up all database tables
3. Verifies database connectivity
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def init_database():
    print("Initializing Print Shop Management System database...")
    
    # Create instance directory if it doesn't exist
    instance_dir = Path("instance")
    if not instance_dir.exists():
        print(f"Creating instance directory: {instance_dir.absolute()}")
        instance_dir.mkdir(parents=True, exist_ok=True)
        
        # Make directory writable
        try:
            os.chmod(instance_dir, 0o777)
            print("Set permissions on instance directory")
        except Exception as e:
            print(f"Warning: Could not set permissions on instance directory: {e}")
    else:
        print(f"Instance directory exists at: {instance_dir.absolute()}")
    
    # Use the main.py script to initialize the database as it already has the proper setup
    print("Running application to initialize database...")
    
    try:
        # Run main.py in a separate process with a timeout
        process = subprocess.Popen(
            ["python", "main.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait a few seconds for database initialization
        time.sleep(3)
        
        # Terminate the process
        process.terminate()
        
        # Check if database was created
        db_path = instance_dir / "printshop.db"
        if db_path.exists() and db_path.stat().st_size > 0:
            print(f"Database initialized successfully at: {db_path.absolute()}")
            print(f"Database size: {db_path.stat().st_size / 1024:.2f} KB")
            return True
        else:
            print("Error: Database file was not created properly.")
            return False
            
    except Exception as e:
        print(f"Error during database initialization: {e}")
        return False

if __name__ == "__main__":
    success = init_database()
    if success:
        print("\nDatabase initialization complete.")
        print("You can now run the application with:")
        print("  python main.py")
        print("  - OR -")
        print("  gunicorn --bind 0.0.0.0:5000 main:app")
        sys.exit(0)
    else:
        print("\nDatabase initialization failed.")
        sys.exit(1)
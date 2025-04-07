#!/usr/bin/env python3
"""
Fix Database Metadata

This script fixes database metadata issues by reloading SQLAlchemy's metadata
for the Order table and verifying all columns are properly mapped.

Usage:
    python fix_db_metadata.py
"""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, MetaData, Table, inspect
from sqlalchemy.ext.declarative import declarative_base

# Load environment variables
load_dotenv()

def fix_db_metadata():
    """Fix database metadata issues"""
    # Get database connection string from environment
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("Error: DATABASE_URL environment variable not set.")
        return False
    
    print(f"Database URL: {database_url}")
    
    try:
        # Create SQLAlchemy engine
        engine = create_engine(database_url)
        
        # Create metadata object
        metadata = MetaData()
        
        # Try to reflect the Order table
        print("Reflecting Order table metadata...")
        order_table = Table('order', metadata, autoload_with=engine)
        
        # Check that required columns exist in reflected metadata
        print("\nVerifying columns in reflected metadata:")
        columns = [c.name for c in order_table.columns]
        print(f"Found {len(columns)} columns:")
        for col in columns:
            print(f"  - {col}")
        
        # Check for specifically required columns
        required_columns = ['is_picked_up', 'pickup_date', 'pickup_by', 
                           'pickup_signature', 'pickup_signature_name', 'tracking_code']
        
        missing_columns = [col for col in required_columns if col not in columns]
        if missing_columns:
            print("\n❌ Missing columns in metadata:")
            for col in missing_columns:
                print(f"  - {col}")
            print("\nAttempting to fix by forcing refresh...")
        else:
            print("\n✅ All required columns found in metadata")
        
        # Manually verify with SQLAlchemy inspector
        print("\nVerifying with SQLAlchemy inspector:")
        insp = inspect(engine)
        inspector_columns = [col['name'] for col in insp.get_columns('order')]
        print(f"Found {len(inspector_columns)} columns via inspector:")
        for col in inspector_columns:
            print(f"  - {col}")
        
        # Warm up the database connection
        print("\nWarming up database connection...")
        with engine.connect() as conn:
            from sqlalchemy.sql import text
            result = conn.execute(text("SELECT * FROM \"order\" LIMIT 1")).fetchone()
            print(f"Connected successfully and retrieved a sample row.")
        
        # Force a metadata clear and reload
        print("\nForcing metadata refresh...")
        metadata.clear()
        metadata = MetaData()
        metadata.reflect(bind=engine)
        
        # Double-check after refresh
        order_table = metadata.tables.get('order')
        if order_table:
            refreshed_columns = [c.name for c in order_table.columns]
            print(f"\nAfter refresh, found {len(refreshed_columns)} columns:")
            for col in refreshed_columns:
                print(f"  - {col}")
            
            missing_after_refresh = [col for col in required_columns if col not in refreshed_columns]
            if missing_after_refresh:
                print("\n❌ Columns still missing after refresh:")
                for col in missing_after_refresh:
                    print(f"  - {col}")
            else:
                print("\n✅ All required columns found after metadata refresh")
        else:
            print("\n❌ Failed to reflect Order table after metadata refresh")
        
        # Create a Base model with the refreshed metadata
        Base = declarative_base(metadata=metadata)
        print("\nCreated a new declarative base with refreshed metadata")
        
        print("\n✅ Database metadata refresh completed")
        return True
    
    except Exception as e:
        print(f"\nError fixing database metadata: {e}")
        return False

if __name__ == "__main__":
    print("=== Database Metadata Fix ===")
    if fix_db_metadata():
        print("\nMetadata fix completed successfully.")
        print("Please restart your application for changes to take effect.")
    else:
        print("\nMetadata fix failed. Please check the error messages above.")
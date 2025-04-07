#!/usr/bin/env python3
"""
Reload SQLAlchemy Metadata

This script attempts to reload SQLAlchemy metadata to
sync the Python model with the actual database structure.
"""

import os
import sys
from importlib import reload
from dotenv import load_dotenv

def main():
    """Update SQLAlchemy metadata to reflect the database structure."""
    # Load environment variables
    load_dotenv()
    
    # Print start message
    print("Reload SQLAlchemy Metadata Script")
    print("=================================")
    
    # Import only the necessary modules
    print("Importing app components...")
    try:
        from app import app, db
        import models
    except Exception as e:
        print(f"Error importing application: {e}")
        return False
    
    # Try to detect the issue
    print("\nAnalyzing models and database structure...")
    try:
        # Get a list of all columns in the Order model
        order_columns = []
        for column in models.Order.__table__.columns:
            order_columns.append(column.name)
        
        print(f"Order model has these columns: {', '.join(order_columns)}")
        
        # Check if pickup columns are in the model
        pickup_columns = ['is_picked_up', 'pickup_date', 'pickup_by', 
                         'pickup_signature', 'pickup_signature_name', 'tracking_code']
        
        missing_in_model = []
        for col in pickup_columns:
            if col not in order_columns:
                missing_in_model.append(col)
        
        if missing_in_model:
            print(f"\nWARNING: These columns are missing in the Order model: {', '.join(missing_in_model)}")
            print("This suggests a model-database mismatch.")
        else:
            print("\nThe Order model contains all required pickup columns.")
        
        # Try to refresh metadata
        print("\nAttempting to refresh database metadata...")
        with app.app_context():
            print("Reflecting database tables...")
            db.metadata.reflect(bind=db.engine)
            
            # Check for the 'order' table in metadata
            if 'order' in db.metadata.tables:
                print("Order table found in reflected metadata.")
                
                # Get reflected columns
                reflected_columns = []
                for column in db.metadata.tables['order'].columns:
                    reflected_columns.append(column.name)
                
                print(f"Reflected columns: {', '.join(reflected_columns)}")
                
                # Check for reflected pickup columns
                missing_in_db = []
                for col in pickup_columns:
                    if col not in reflected_columns:
                        missing_in_db.append(col)
                
                if missing_in_db:
                    print(f"\nWARNING: These columns are missing in the database: {', '.join(missing_in_db)}")
                    print("This indicates the database schema doesn't match the model.")
                else:
                    print("\nAll required pickup columns exist in the database.")
            else:
                print("WARNING: Order table not found in reflected metadata.")
    
    except Exception as e:
        print(f"Error analyzing models: {e}")
    
    # Try to clear SQLAlchemy cached data
    print("\nAttempting to clear SQLAlchemy cache...")
    try:
        with app.app_context():
            # Clear session
            print("Clearing session...")
            db.session.close()
            db.session.remove()
            
            # Dispose engine connections
            print("Disposing engine connections...")
            db.engine.dispose()
            
            # Refresh metadata
            print("Refreshing metadata...")
            db.metadata.clear()
            db.metadata.reflect(bind=db.engine)
            
            print("Cache cleared and metadata refreshed.")
    except Exception as e:
        print(f"Error clearing cache: {e}")
    
    # Suggest next steps
    print("\nNext steps:")
    print("1. Try restarting your Flask application now")
    print("2. If issues persist, check models.py to ensure Order model includes all pickup fields")
    print("3. For model definition issues, run: python update_order_pickup_fields.py (if available)")
    print("4. As a last resort, restart the server completely")
    
    return True

if __name__ == "__main__":
    main()
    print("\nScript completed. Please restart your application.")
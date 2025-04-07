#!/usr/bin/env python3
"""
Fix Order Table Name Issue

This script directly addresses the issue where 'order' is a reserved word in PostgreSQL
by modifying the database connection options to properly quote identifiers.

Usage:
    python fix_order_name_issue.py
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def update_app_file():
    """Update app.py with proper PostgreSQL identifier quoting"""
    app_path = 'app.py'
    
    if not os.path.exists(app_path):
        print(f"Error: {app_path} not found.")
        return False
    
    try:
        # Read the current content
        with open(app_path, 'r') as f:
            content = f.read()
        
        # Check if we already have the configuration
        if 'quote_schema=True' in content and 'quote_all=True' in content:
            print("✅ SQLAlchemy quoting configuration already in place.")
            return True
            
        # Find the block with SQLALCHEMY_ENGINE_OPTIONS
        if 'app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {' in content:
            # Add the quote settings to the dict
            new_content = content.replace(
                'app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {',
                'app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {\n    "connect_args": {"options": "-c timezone=utc"},\n    "quote_schema": True,\n    "quote_all": True,'
            )
            
            # Write back
            with open(app_path, 'w') as f:
                f.write(new_content)
                
            print("✅ Added identifier quoting to SQLAlchemy engine options.")
            return True
        else:
            print("❌ Could not find SQLALCHEMY_ENGINE_OPTIONS in app.py.")
            return False
            
    except Exception as e:
        print(f"Error updating app.py: {e}")
        return False

def update_models_file():
    """Update models.py to set explicit table name for Order"""
    models_path = 'models.py'
    
    if not os.path.exists(models_path):
        print(f"Error: {models_path} not found.")
        return False
    
    try:
        # Read the current content
        with open(models_path, 'r') as f:
            content = f.read()
        
        # Check if we already have an explicit table name
        if '__tablename__' in content and 'Order(db.Model)' in content:
            print("✅ Order model already has explicit table name.")
            return True
        
        # Find the Order class definition
        if 'class Order(db.Model):' in content:
            # Add the __tablename__ attribute to the class
            new_content = content.replace(
                'class Order(db.Model):',
                'class Order(db.Model):\n    __tablename__ = "order"  # Explicitly set table name with quotes handled by SQLAlchemy'
            )
            
            # Write back
            with open(models_path, 'w') as f:
                f.write(new_content)
                
            print("✅ Added explicit table name to Order model.")
            return True
        else:
            print("❌ Could not find Order class in models.py.")
            return False
            
    except Exception as e:
        print(f"Error updating models.py: {e}")
        return False

def create_schema_test_script():
    """Create a script to test model and schema initialization"""
    test_path = 'test_schema.py'
    
    script_content = """#!/usr/bin/env python3
\"\"\"
Test Schema Script

This script tests the database schema initialization with proper identifier quoting.
\"\"\"

import os
from dotenv import load_dotenv
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

# Load environment variables
load_dotenv()

class Base(DeclarativeBase):
    pass

# Create test app
db = SQLAlchemy(model_class=Base)
app = Flask(__name__)

# Configure database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
    "connect_args": {"options": "-c timezone=utc"},
    "quote_schema": True,
    "quote_all": True
}

# Initialize app
db.init_app(app)

class TestOrder(db.Model):
    __tablename__ = "order"  # Explicitly set table name
    
    id = db.Column(db.Integer, primary_key=True)
    test_column = db.Column(db.String(50))
    is_picked_up = db.Column(db.Boolean, default=False)

with app.app_context():
    # Test reflecting the existing table
    print("Testing schema connection...")
    try:
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        columns = inspector.get_columns("order")
        print(f"Found {len(columns)} columns in 'order' table:")
        for col in columns:
            print(f"  - {col['name']} ({col['type']})")
            
        # Test a simple query
        from sqlalchemy import text
        with db.engine.connect() as conn:
            result = conn.execute(text('SELECT id, is_picked_up FROM "order" LIMIT 1')).fetchone()
            print(f"\\nTest query result: {result}")
            
        print("\\n✅ Schema test completed successfully.")
    except Exception as e:
        print(f"\\n❌ Schema test error: {e}")
"""
    
    try:
        with open(test_path, 'w') as f:
            f.write(script_content)
        
        print(f"✅ Created schema test script: {test_path}")
        return True
    except Exception as e:
        print(f"Error creating test script: {e}")
        return False

def main():
    """Run all fixes"""
    print("=== Fixing Order Table Name Issue ===")
    
    # Update app.py with proper quoting
    app_updated = update_app_file()
    
    # Update models.py with explicit table name
    models_updated = update_models_file()
    
    # Create test script
    test_created = create_schema_test_script()
    
    if app_updated and models_updated and test_created:
        print("\n✅ All updates completed successfully.")
        print("\nYou can now run the test script to verify the schema:")
        print("  python test_schema.py")
        print("\nThen restart your application:")
        print("  python main.py")
        return 0
    else:
        print("\n❌ Some updates failed. Please check the error messages above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
#!/usr/bin/env python3
"""
Test Schema Script

This script tests the database schema initialization with proper identifier quoting.
"""

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
            print(f"\nTest query result: {result}")
            
        print("\n✅ Schema test completed successfully.")
    except Exception as e:
        print(f"\n❌ Schema test error: {e}")

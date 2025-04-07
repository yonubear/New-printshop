"""
Update the quotes database schema to add the missing columns for QuoteItem

This script adds the product_type and related booklet columns to the QuoteItem table.
"""
import os
from app import app, db
from sqlalchemy import text

def update_database():
    """Add missing columns to the QuoteItem table"""
    with app.app_context():
        # Check if the column already exists
        try:
            db.session.execute(text("SELECT product_type FROM quote_item LIMIT 1"))
            print("Column 'product_type' already exists. No update needed.")
            return
        except Exception:
            print("Column 'product_type' doesn't exist. Adding missing columns...")
        
        # Add the new columns
        statements = [
            "ALTER TABLE quote_item ADD COLUMN product_type VARCHAR(50) DEFAULT 'print_job'",
            "ALTER TABLE quote_item ADD COLUMN page_count INTEGER",
            "ALTER TABLE quote_item ADD COLUMN cover_paper_type VARCHAR(100)",
            "ALTER TABLE quote_item ADD COLUMN binding_type VARCHAR(50)",
            "ALTER TABLE quote_item ADD COLUMN cover_printing VARCHAR(20)",
            "ALTER TABLE quote_item ADD COLUMN self_cover BOOLEAN DEFAULT 0"
        ]
        
        for statement in statements:
            try:
                db.session.execute(text(statement))
                print(f"Executed: {statement}")
            except Exception as e:
                print(f"Error executing {statement}: {e}")
        
        # Commit the changes
        db.session.commit()
        print("Database schema updated successfully!")

if __name__ == "__main__":
    update_database()
#!/usr/bin/env python3
"""
Update Paper Options Cost Field

This script adds the cost_per_sheet field to the PaperOption model and updates existing records.
It provides a simple way to migrate existing paper option data without losing any information.

Usage:
    python update_paper_cost.py
"""

import os
import sys
import sqlite3

# Ensure we're pointing to the correct database file
DB_PATH = 'instance/printshop.db'

def check_column_exists():
    """Check if the cost_per_sheet column already exists in the table"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(paper_option)")
        columns = [col[1] for col in cursor.fetchall()]
        conn.close()
        return 'cost_per_sheet' in columns
    except Exception as e:
        print(f"Error checking column: {e}")
        return False

def add_cost_column():
    """Add the cost_per_sheet column to the paper_option table"""
    try:
        # Connect directly to the SQLite database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check if column exists first (SQLite doesn't have IF NOT EXISTS for ALTER TABLE)
        cursor.execute("PRAGMA table_info(paper_option)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'cost_per_sheet' not in columns:
            # Add the column
            cursor.execute('ALTER TABLE paper_option ADD COLUMN cost_per_sheet FLOAT DEFAULT 0.0')
            conn.commit()
            print("Successfully added cost_per_sheet column to paper_option table")
        else:
            print("Column cost_per_sheet already exists")
            
        conn.close()
        return True
    except Exception as e:
        print(f"Error adding column: {e}")
        return False

def update_cost_values():
    """Update existing records with default cost values based on price"""
    try:
        # Connect directly to the SQLite database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get all paper options with cost = 0 and price > 0
        cursor.execute("SELECT id, price_per_sheet FROM paper_option WHERE cost_per_sheet = 0 AND price_per_sheet > 0")
        paper_options = cursor.fetchall()
        
        update_count = 0
        for option in paper_options:
            option_id, price = option
            # Default cost is 70% of price (30% margin)
            cost = round(price * 0.7, 4)
            cursor.execute("UPDATE paper_option SET cost_per_sheet = ? WHERE id = ?", (cost, option_id))
            update_count += 1
        
        conn.commit()
        conn.close()
        
        print(f"Updated {update_count} paper options with estimated cost values")
        return True
    except Exception as e:
        print(f"Error updating cost values: {e}")
        return False

def main():
    """Main function"""
    print("Starting paper cost field update...")
    
    # Check if column exists
    if check_column_exists():
        print("Cost per sheet column already exists")
    else:
        print("Adding cost_per_sheet column...")
        if not add_cost_column():
            print("Failed to add column, exiting")
            return False
    
    print("Updating cost values for existing paper options...")
    if not update_cost_values():
        print("Failed to update cost values")
        return False
    
    print("Paper cost field update completed successfully!")
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)
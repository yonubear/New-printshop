"""
Update the database schema to add the finish_size column to the QuoteItem table.
"""
import os
import sqlite3

def update_database():
    """Add finish_size column to the QuoteItem table"""
    db_path = 'instance/printshop.db'
    
    # Check if the database file exists
    if not os.path.exists(db_path):
        print(f"Database file not found at {db_path}")
        return
    
    # Connect to the database directly
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if the column already exists
    try:
        cursor.execute("PRAGMA table_info(quote_item)")
        columns = cursor.fetchall()
        column_names = [column[1] for column in columns]
        
        if 'finish_size' in column_names:
            print("Column 'finish_size' already exists. No update needed.")
            conn.close()
            return
        
        print("Column 'finish_size' doesn't exist. Adding the column...")
        
        # Add the new column
        statement = "ALTER TABLE quote_item ADD COLUMN finish_size VARCHAR(50)"
        cursor.execute(statement)
        print(f"Executed: {statement}")
        
        # Commit the changes
        conn.commit()
        print("Database schema updated successfully!")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    update_database()
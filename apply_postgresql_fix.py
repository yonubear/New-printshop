#!/usr/bin/env python3
"""
PostgreSQL Database Fix Script Runner

This script reads the SQL fix script and applies it to your PostgreSQL database
using the settings from your environment variables.
"""

import os
import sys
import psycopg2
from dotenv import load_dotenv

def apply_database_fix():
    """
    Apply the database fix SQL script to the PostgreSQL database
    using environment variables for connection details.
    """
    # Load environment variables from .env file
    load_dotenv()
    
    # Get database connection details from environment variables
    db_url = os.environ.get('DATABASE_URL')
    
    if not db_url:
        # Try to construct from individual parts
        db_host = os.environ.get('PGHOST', 'localhost')
        db_port = os.environ.get('PGPORT', '5432')
        db_name = os.environ.get('PGDATABASE', 'printshop')
        db_user = os.environ.get('PGUSER', 'postgres')
        db_password = os.environ.get('PGPASSWORD', '')
        
        db_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    
    print("Connecting to database...")
    
    try:
        # Connect to the database
        conn = psycopg2.connect(db_url)
        conn.autocommit = False
        cursor = conn.cursor()
        
        # Read the SQL script
        script_path = "fix_printshop_postgresql_database.sql"
        if not os.path.exists(script_path):
            print(f"Error: SQL script file '{script_path}' not found.")
            return False
        
        print(f"Reading SQL script from {script_path}...")
        with open(script_path, 'r') as f:
            sql_script = f.read()
        
        # Remove the \echo commands which are psql-specific and not valid in regular SQL
        lines = sql_script.split('\n')
        filtered_lines = []
        for line in lines:
            if not line.strip().startswith('\\echo'):
                filtered_lines.append(line)
        
        # Split the script into statements
        statements = '\n'.join(filtered_lines).split(';')
        
        # Execute each statement
        print("Applying database fixes...")
        success_count = 0
        error_count = 0
        
        for i, statement in enumerate(statements):
            if statement.strip():
                try:
                    cursor.execute(statement)
                    success_count += 1
                    if i % 10 == 0:
                        print(f"Processed {i+1}/{len(statements)} statements...")
                except Exception as e:
                    error_count += 1
                    print(f"Error executing statement: {e}")
                    print(f"Statement was: {statement[:100]}...")
        
        # Commit the transaction
        conn.commit()
        print(f"Database fix applied successfully! {success_count} statements executed, {error_count} errors.")
        
        # Verify the changes
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_schema = 'public' AND table_name = 'order'
            AND column_name IN ('is_picked_up', 'pickup_date', 'pickup_by', 'pickup_signature', 'pickup_signature_name', 'tracking_code')
        """)
        columns = cursor.fetchall()
        
        if columns:
            print("Verification successful! The following pickup columns exist:")
            for col in columns:
                print(f"- {col[0]}")
        else:
            print("Verification failed: No pickup columns found in the order table.")
        
        return True
    
    except Exception as e:
        print(f"Error: {e}")
        return False
    finally:
        if 'conn' in locals() and conn:
            conn.close()
            print("Database connection closed.")

if __name__ == "__main__":
    print("Print Shop PostgreSQL Database Fix Script Runner")
    print("===============================================")
    
    success = apply_database_fix()
    
    if success:
        print("Database fix operation completed successfully.")
        sys.exit(0)
    else:
        print("Database fix operation failed. Please check the error messages above.")
        sys.exit(1)
#!/usr/bin/env python3
"""
Diagnose Specific Order Table Issues

This script checks for specific issues with the Order table
in the PostgreSQL database, focusing on pickup-related column conflicts.

Usage:
    python diagnose_specific_order_issues.py
"""

import os
import sys
from dotenv import load_dotenv
import psycopg2

# Load environment variables
load_dotenv()

def diagnose_order_table():
    """Diagnose specific issues with Order table in PostgreSQL database"""
    # Get database connection string from environment
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("Error: DATABASE_URL environment variable not set.")
        return False
    
    print(f"Database URL: {database_url}")
    
    # Check if this is a PostgreSQL database
    if not database_url.startswith('postgresql://'):
        print("Error: This script is intended for PostgreSQL databases only.")
        print(f"Current DATABASE_URL: {database_url}")
        return False
    
    try:
        # Connect to PostgreSQL database
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        # 1. Check order table structure
        print("\nChecking Order table structure:")
        cursor.execute("""
            SELECT column_name, data_type, character_maximum_length, 
                   column_default, is_nullable, is_updatable
            FROM information_schema.columns 
            WHERE table_schema = 'public' AND table_name = 'order' 
            ORDER BY ordinal_position
        """)
        
        columns = cursor.fetchall()
        print(f"Found {len(columns)} columns in Order table:")
        for col in columns:
            col_name, data_type, max_length, default, nullable, updatable = col
            print(f"  - {col_name}: {data_type}" + 
                  (f"({max_length})" if max_length else "") + 
                  f", {'NULL' if nullable == 'YES' else 'NOT NULL'}" +
                  (f", DEFAULT {default}" if default else "") +
                  (", READ ONLY" if updatable == 'NO' else ""))
        
        # 2. Check for case sensitivity issues
        print("\nChecking for case sensitivity issues:")
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_schema = 'public' AND table_name = 'order' 
            AND column_name ILIKE '%picked%' 
            ORDER BY column_name
        """)
        pickup_columns = cursor.fetchall()
        print(f"Found {len(pickup_columns)} pickup-related columns:")
        for col in pickup_columns:
            print(f"  - {col[0]}")
            
        # 3. Check for view definitions that might cause issues
        print("\nChecking for views that reference the Order table:")
        cursor.execute("""
            SELECT v.table_name, v.view_definition
            FROM information_schema.views v
            WHERE v.table_schema = 'public'
            AND v.view_definition ILIKE '%order%'
        """)
        views = cursor.fetchall()
        if views:
            print(f"Found {len(views)} views referencing the Order table:")
            for view in views:
                print(f"  - {view[0]}")
                # print(f"    Definition: {view[1][:100]}...") # First 100 chars of definition
        else:
            print("No views found that reference the Order table.")
        
        # 4. Try a specific query with the is_picked_up column
        print("\nTesting a query with is_picked_up column:")
        try:
            cursor.execute('SELECT id, order_number, is_picked_up FROM "order" LIMIT 1')
            result = cursor.fetchone()
            if result:
                print(f"  ✅ Query successful: {result}")
            else:
                print("  ✅ Query successful but no rows returned")
        except Exception as e:
            print(f"  ❌ Query failed: {e}")
        
        # 5. Check for any triggers on the table
        print("\nChecking for triggers on the Order table:")
        cursor.execute("""
            SELECT trigger_name, event_manipulation, action_statement
            FROM information_schema.triggers
            WHERE event_object_schema = 'public' AND event_object_table = 'order'
        """)
        triggers = cursor.fetchall()
        if triggers:
            print(f"Found {len(triggers)} triggers on the Order table:")
            for trigger in triggers:
                print(f"  - {trigger[0]} (on {trigger[1]})")
                # print(f"    Action: {trigger[2][:100]}...") # First 100 chars of action
        else:
            print("No triggers found on the Order table.")
            
        # 6. Check for any object permissions that might be causing issues
        print("\nChecking for permission issues:")
        cursor.execute("""
            SELECT grantee, privilege_type
            FROM information_schema.table_privileges
            WHERE table_schema = 'public' AND table_name = 'order'
        """)
        privileges = cursor.fetchall()
        if privileges:
            print(f"Found permissions for the Order table:")
            for priv in privileges:
                print(f"  - {priv[0]} has {priv[1]} permission")
        else:
            print("No explicit permissions found for the Order table.")
            
        # 7. Verify the actual data in the table
        print("\nChecking a sample row from the Order table:")
        cursor.execute("""
            SELECT CAST(is_picked_up AS TEXT), 
                   CAST(pickup_date AS TEXT), 
                   pickup_by, 
                   SUBSTRING(pickup_signature, 1, 30) 
            FROM "order" 
            LIMIT 1
        """)
        sample = cursor.fetchone()
        if sample:
            print(f"  Sample row values:")
            print(f"  - is_picked_up: {sample[0]}")
            print(f"  - pickup_date: {sample[1]}")
            print(f"  - pickup_by: {sample[2]}")
            print(f"  - pickup_signature (truncated): {sample[3]}...")
        else:
            print("  No rows found in the Order table.")
        
        # Close connection
        cursor.close()
        conn.close()
        
        return True
    except Exception as e:
        print(f"Error diagnosing database: {e}")
        if 'conn' in locals() and conn:
            conn.close()
        return False

if __name__ == "__main__":
    print("=== Order Table Diagnostic Tool ===")
    diagnose_order_table()
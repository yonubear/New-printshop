#!/usr/bin/env python3
"""
Database Connection Test

This script tests the database connection directly, bypassing the Flask application.
It will help identify issues with database configuration and permissions.
Compatible with both SQLite and PostgreSQL databases.

Usage:
    python test_db_connection.py
"""

import os
import sys
from pathlib import Path
import time
import shutil
import re
import sqlite3

# Import PostgreSQL driver conditionally
try:
    import psycopg2
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False

def check_environment():
    """Check environment variables and .env file"""
    print("\n=== Checking Environment Configuration ===")
    
    # Check for .env file
    env_file = Path('.env')
    if not env_file.exists():
        print("❌ .env file not found")
        print("Creating a basic .env file with SQLite configuration...")
        with open(env_file, 'w') as f:
            f.write("DATABASE_URL=sqlite:///instance/printshop.db\n")
        print("✅ Created .env file with default SQLite configuration")
    else:
        print("✅ .env file exists")
        
        # Check content of .env file
        with open(env_file, 'r') as f:
            content = f.read()
            
        print("\n.env file content:")
        db_url_found = False
        
        for line in content.splitlines():
            if line.strip() and not line.startswith('#'):
                if 'DATABASE_URL' in line:
                    db_url_found = True
                    print(f"  → {line}")
                    
                    # Check if DATABASE_URL is correctly configured for SQLite
                    if 'sqlite:///printshop.db' in line and 'sqlite:///instance/printshop.db' not in line:
                        print("⚠️  SQLite DATABASE_URL is using incorrect path (missing instance/)")
                        
                        # Correct the path
                        corrected = content.replace('sqlite:///printshop.db', 'sqlite:///instance/printshop.db')
                        with open(env_file, 'w') as f:
                            f.write(corrected)
                        print("✅ Fixed DATABASE_URL to use instance/ directory")
                    elif 'postgresql://' in line:
                        print("✅ PostgreSQL database configuration detected")
                elif 'PGDATABASE' in line or 'PGUSER' in line or 'PGPASSWORD' in line or 'PGHOST' in line:
                    print(f"  → Found PostgreSQL environment variable: {line.split('=')[0]}")
        
        if not db_url_found:
            print("⚠️  DATABASE_URL not found in .env file")
            
            # Check if we have PostgreSQL variables instead
            pg_vars = [
                'PGDATABASE' in content,
                'PGUSER' in content,
                'PGPASSWORD' in content,
                'PGHOST' in content
            ]
            
            if any(pg_vars):
                print("ℹ️  Found PostgreSQL configuration variables, but no DATABASE_URL")
                print("   This is OK if the application uses these variables directly")
    
    # Check environment variables
    db_url = os.environ.get('DATABASE_URL')
    pg_vars_present = all([
        os.environ.get('PGDATABASE'),
        os.environ.get('PGUSER'),
        os.environ.get('PGPASSWORD'),
        os.environ.get('PGHOST')
    ])
    
    # Database configuration detection
    if db_url:
        print(f"✅ DATABASE_URL environment variable is set")
        if 'sqlite:' in db_url:
            print(f"   Database type: SQLite")
            # Set it correctly if needed
            if 'sqlite:///printshop.db' in db_url and 'sqlite:///instance/printshop.db' not in db_url:
                correct_url = db_url.replace('sqlite:///printshop.db', 'sqlite:///instance/printshop.db')
                os.environ['DATABASE_URL'] = correct_url
                print(f"✅ Fixed DATABASE_URL environment variable: {correct_url}")
        elif 'postgresql:' in db_url:
            print(f"   Database type: PostgreSQL")
            # Check if we have the psycopg2 driver
            if not PSYCOPG2_AVAILABLE:
                print("⚠️  PostgreSQL driver (psycopg2) is not installed")
                print("   Run: pip install psycopg2-binary")
        else:
            print(f"   Database type: Other ({db_url.split(':')[0]})")
    elif pg_vars_present:
        print("✅ PostgreSQL environment variables are set (PGDATABASE, PGUSER, etc.)")
        if not PSYCOPG2_AVAILABLE:
            print("⚠️  PostgreSQL driver (psycopg2) is not installed")
            print("   Run: pip install psycopg2-binary")
        
        # Construct a DATABASE_URL from PG variables for SQLAlchemy
        pg_host = os.environ.get('PGHOST')
        pg_port = os.environ.get('PGPORT', '5432')
        pg_user = os.environ.get('PGUSER')
        pg_pass = os.environ.get('PGPASSWORD')
        pg_db = os.environ.get('PGDATABASE')
        
        db_url = f"postgresql://{pg_user}:{pg_pass}@{pg_host}:{pg_port}/{pg_db}"
        os.environ['DATABASE_URL'] = db_url
        print(f"✅ Constructed DATABASE_URL from PostgreSQL variables")
    else:
        print("⚠️  No database configuration found in environment variables")
        
        # Try to read from .env file
        if env_file.exists():
            with open(env_file, 'r') as f:
                for line in f:
                    if line.startswith('DATABASE_URL='):
                        db_url = line.split('=', 1)[1].strip()
                        os.environ['DATABASE_URL'] = db_url
                        print(f"✅ Set DATABASE_URL from .env file: {db_url}")
                        break
        
        # Set a default if still not set
        if not os.environ.get('DATABASE_URL'):
            os.environ['DATABASE_URL'] = 'sqlite:///instance/printshop.db'
            print("✅ Set default DATABASE_URL: sqlite:///instance/printshop.db")
    
    return True

def check_instance_directory():
    """Check if instance directory exists and is writable"""
    print("\n=== Checking Instance Directory ===")
    
    instance_dir = Path('instance')
    
    # Check if directory exists
    if not instance_dir.exists():
        print("❌ Instance directory does not exist")
        print("Creating instance directory...")
        try:
            instance_dir.mkdir(exist_ok=True)
            print("✅ Created instance directory")
        except Exception as e:
            print(f"❌ Failed to create instance directory: {e}")
            return False
    else:
        print("✅ Instance directory exists")
    
    # Check if directory is writable
    try:
        test_file = instance_dir / 'test_write.tmp'
        with open(test_file, 'w') as f:
            f.write('test')
        test_file.unlink()  # Remove test file
        print("✅ Instance directory is writable")
    except Exception as e:
        print(f"❌ Instance directory is not writable: {e}")
        try:
            os.chmod(instance_dir, 0o777)
            print("✅ Updated instance directory permissions")
        except Exception as e:
            print(f"❌ Failed to update permissions: {e}")
            return False
    
    return True

def check_database_file():
    """Check if database file exists and is accessible"""
    print("\n=== Checking Database Connection ===")
    
    # Get expected database path
    db_url = os.environ.get('DATABASE_URL', 'sqlite:///instance/printshop.db')
    
    # Check if we're using PostgreSQL
    if 'postgresql://' in db_url:
        if not PSYCOPG2_AVAILABLE:
            print("❌ PostgreSQL driver (psycopg2) is not installed")
            print("   Run: pip install psycopg2-binary")
            return False
            
        print("🔍 Testing PostgreSQL connection...")
        
        # Extract connection parameters from URL
        try:
            # Remove postgresql:// prefix
            conn_str = db_url.replace('postgresql://', '')
            
            # Extract username and password
            if '@' in conn_str:
                auth, rest = conn_str.split('@', 1)
                if ':' in auth:
                    username, password = auth.split(':', 1)
                else:
                    username = auth
                    password = ''
            else:
                username = ''
                password = ''
                rest = conn_str
                
            # Extract host, port and database
            if '/' in rest:
                hostport, database = rest.split('/', 1)
                if ':' in hostport:
                    host, port = hostport.split(':', 1)
                    port = int(port)
                else:
                    host = hostport
                    port = 5432
            else:
                host = rest
                port = 5432
                database = ''
            
            # If there are query parameters, remove them
            if '?' in database:
                database = database.split('?', 1)[0]
            
            print(f"   Host: {host}")
            print(f"   Port: {port}")
            print(f"   Database: {database}")
            print(f"   Username: {username}")
            
            # Attempt to connect
            conn = psycopg2.connect(
                host=host,
                port=port,
                database=database,
                user=username,
                password=password
            )
            
            # Create a test table
            cursor = conn.cursor()
            cursor.execute("CREATE TABLE IF NOT EXISTS db_test (id SERIAL PRIMARY KEY, test_time TEXT)")
            conn.commit()
            
            # Insert test data
            cursor.execute("INSERT INTO db_test (test_time) VALUES (%s) RETURNING id", (time.ctime(),))
            conn.commit()
            
            # Verify the data was inserted
            cursor.execute("SELECT COUNT(*) FROM db_test")
            count = cursor.fetchone()[0]
            
            # Get all tables in the public schema
            cursor.execute("""
                SELECT tablename FROM pg_tables 
                WHERE schemaname = 'public'
            """)
            tables = [row[0] for row in cursor.fetchall()]
            
            conn.close()
            
            print(f"✅ Successfully connected to PostgreSQL database and executed queries")
            print(f"   Tables found: {', '.join(tables)}")
            print(f"   Test write succeeded ({count} records in db_test table)")
            
            return True
        except Exception as e:
            print(f"❌ Failed to connect to PostgreSQL database: {e}")
            print("\nCheck your PostgreSQL configuration:")
            print("1. Make sure the PostgreSQL server is running")
            print("2. Verify the connection details in DATABASE_URL")
            print("3. Check that your user has proper permissions")
            print("4. Ensure the database exists")
            return False
    
    # For SQLite databases
    if 'sqlite://' in db_url:
        print("🔍 Testing SQLite database...")
        
        # Extract path from SQLite URL
        if 'sqlite:///instance/printshop.db' in db_url:
            db_path = Path('instance/printshop.db')
        elif 'sqlite:///printshop.db' in db_url:
            db_path = Path('printshop.db')
            print("⚠️  Database path does not include instance directory")
            print("Changing database path to instance/printshop.db")
            db_path = Path('instance/printshop.db')
        else:
            # Extract the path
            path_part = db_url.split('sqlite:///', 1)[1]
            db_path = Path(path_part)
        
        # Check for root-level database file that might be causing confusion
        root_db = Path('printshop.db')
        if root_db.exists():
            print(f"⚠️  Found database file in root directory: {root_db}")
            print("This may cause confusion with the instance directory database.")
            
            # Check if it's non-empty
            if root_db.stat().st_size > 0:
                print(f"⚠️  Root directory database file is non-empty ({root_db.stat().st_size} bytes)")
                
                # If instance DB doesn't exist, move this one
                if not db_path.exists() and root_db.stat().st_size > 100:
                    print("Moving root database to instance directory...")
                    db_path.parent.mkdir(exist_ok=True)
                    shutil.copy2(root_db, db_path)
                    print(f"✅ Copied database from {root_db} to {db_path}")
                    
                    # Create a backup of the root DB
                    backup = root_db.with_suffix('.db.bak')
                    shutil.copy2(root_db, backup) 
                    print(f"✅ Created backup of root database: {backup}")
                    
                    # Replace root DB with empty file
                    root_db.unlink()
                    root_db.touch()
                    print(f"✅ Replaced root database with empty file")
        
        # Check if database file exists
        if not db_path.exists():
            print(f"❌ Database file not found: {db_path}")
            print("Creating empty database file...")
            try:
                db_path.parent.mkdir(exist_ok=True)
                conn = sqlite3.connect(str(db_path))
                conn.close()
                print(f"✅ Created empty database file: {db_path}")
            except Exception as e:
                print(f"❌ Failed to create database file: {e}")
                return False
        else:
            print(f"✅ Database file exists: {db_path}")
            print(f"   File size: {db_path.stat().st_size} bytes")
            if db_path.stat().st_size == 0:
                print("⚠️  Database file is empty (0 bytes)")
        
        # Check if database file is readable/writable
        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            
            # Try to create a test table
            cursor.execute("CREATE TABLE IF NOT EXISTS db_test (id INTEGER PRIMARY KEY, test_time TEXT)")
            
            # Insert test data
            cursor.execute("INSERT INTO db_test (test_time) VALUES (?)", (time.ctime(),))
            conn.commit()
            
            # Verify data was inserted
            cursor.execute("SELECT COUNT(*) FROM db_test")
            count = cursor.fetchone()[0]
            
            # Get all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            conn.close()
            
            print(f"✅ Successfully connected to SQLite database and executed queries")
            print(f"   Tables found: {', '.join(tables)}")
            print(f"   Test write succeeded ({count} records in db_test table)")
            
            return True
        except Exception as e:
            print(f"❌ Failed to access SQLite database: {e}")
            
            # Check and fix permissions
            try:
                os.chmod(db_path, 0o666)  # Set read/write for everyone
                print(f"✅ Updated database file permissions")
                
                # Try again
                conn = sqlite3.connect(str(db_path))
                conn.close()
                print(f"✅ Successfully connected to database after permission update")
                return True
            except Exception as e:
                print(f"❌ Still unable to access database: {e}")
                return False
    
    # For other database types
    print(f"⚠️  Unsupported database URL type: {db_url}")
    print("   This test script focuses on SQLite and PostgreSQL.")
    print("   For other databases, please refer to the documentation.")
    return False

def test_flask_integration():
    """Test if Flask can connect to the database"""
    print("\n=== Testing Flask Database Integration ===")
    
    try:
        # Try to import Flask app and test database connection
        from app import app, db
        
        with app.app_context():
            # Check if db can execute a query
            from sqlalchemy import text
            result = db.session.execute(text("SELECT 1")).scalar()
            if result == 1:
                print("✅ Flask successfully connected to the database")
                
                # Determine the database type
                db_url = os.environ.get('DATABASE_URL', '')
                
                # Check for required tables based on database type
                is_postgres = 'postgresql://' in db_url
                
                if is_postgres:
                    # PostgreSQL query to list tables in the public schema
                    try:
                        result = db.session.execute(text("""
                            SELECT tablename FROM pg_tables 
                            WHERE schemaname = 'public'
                        """)).fetchall()
                        tables = [row[0] for row in result]
                    except Exception as e:
                        print(f"⚠️  Could not retrieve table list: {e}")
                        tables = []
                else:
                    # SQLite query to list tables
                    try:
                        result = db.session.execute(text("SELECT name FROM sqlite_master WHERE type='table'")).fetchall()
                        tables = [row[0] for row in result]
                    except Exception as e:
                        print(f"⚠️  Could not retrieve table list: {e}")
                        tables = []
                
                # Core tables that should exist
                core_tables = ['customer', 'order', 'paper_option', 'material', 'saved_price']
                missing_tables = [table for table in core_tables if table not in tables]
                
                if missing_tables:
                    print(f"⚠️  Some core tables are missing: {', '.join(missing_tables)}")
                    
                    # Try to create all tables
                    print("Creating database tables...")
                    try:
                        db.create_all()
                        print("✅ Created all database tables")
                    except Exception as e:
                        print(f"❌ Failed to create tables: {e}")
                        return False
                else:
                    print(f"✅ All core tables exist")
                    if tables:
                        print(f"   Tables found: {', '.join(tables)}")
                
                return True
            else:
                print("❌ Flask connected to database but query failed")
                return False
    except Exception as e:
        print(f"❌ Flask database integration test failed: {e}")
        print("   This may indicate a configuration issue in app.py or the database URL")
        if "no module named" in str(e).lower():
            print("   Make sure all required Python packages are installed")
            print("   Check the dependencies.txt file or run: pip install -r dependencies.txt")
        elif "no such table" in str(e).lower():
            print("   Database tables may not exist yet. Try running: python init_db.py")
        return False

def main():
    """Main function to run all tests"""
    print("=== Database Connection Test ===")
    print(f"Current directory: {os.getcwd()}")
    print(f"Python version: {sys.version}")
    
    # Step 1: Check environment
    if not check_environment():
        print("\n❌ Environment check failed")
        return False
    
    # Step 2: Check instance directory
    if not check_instance_directory():
        print("\n❌ Instance directory check failed")
        return False
    
    # Step 3: Check database file
    if not check_database_file():
        print("\n❌ Database file check failed")
        return False
    
    # Step 4: Test Flask integration
    flask_ok = test_flask_integration()
    
    # Final result
    if flask_ok:
        print("\n✅ All tests passed! Your database configuration is working correctly.")
        print("\nYou can now run the application:")
        print("  python main.py")
        return True
    else:
        print("\n⚠️  Some tests failed. Basic database access works, but Flask integration has issues.")
        print("\nTry initializing the database:")
        print("  python init_db.py")
        print("\nThen run the application:")
        print("  python main.py")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
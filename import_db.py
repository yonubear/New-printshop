"""
Import database from SQL file
This utility imports a SQL file into the database for restoring from backup or migration.
"""
import os
import argparse
import re
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def import_database(input_file):
    """
    Import database schema and data from SQL file
    
    Args:
        input_file: Path to input SQL file
    
    Returns:
        Boolean indicating success
    """
    if not os.path.exists(input_file):
        print(f"Error: File {input_file} not found")
        return False
    
    # Get database URL from environment or use SQLite as fallback
    database_url = os.environ.get('DATABASE_URL')
    
    if not database_url:
        db_path = os.path.join('instance', 'printshop.db')
        database_url = f"sqlite:///{db_path}"
    
    # Connect to database
    engine = create_engine(database_url)
    
    # Read SQL file content
    with open(input_file, 'r') as f:
        sql_content = f.read()
    
    # Split SQL content into individual statements
    # This is a simple approach and might not work for complex SQL files
    sql_statements = re.split(r';\s*\n', sql_content)
    
    try:
        with engine.connect() as conn:
            # Begin transaction
            with conn.begin():
                for statement in sql_statements:
                    # Skip empty statements and comments
                    if not statement.strip() or statement.strip().startswith('--'):
                        continue
                    
                    # Execute statement
                    conn.execute(text(statement))
        
        print(f"Database imported successfully from {input_file}")
        return True
    
    except Exception as e:
        print(f"Error importing database: {str(e)}")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Import database from SQL file')
    parser.add_argument('input', help='Input SQL file path')
    args = parser.parse_args()
    
    import_database(args.input)
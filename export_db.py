"""
Export database to SQL file
This utility creates a SQL export of the database for backup or migration purposes.
"""
import os
import datetime
import argparse
from sqlalchemy import create_engine, MetaData, Table, select
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def export_database(output_file=None):
    """
    Export database schema and data to SQL file
    
    Args:
        output_file: Path to output file. If None, a timestamped file is created.
    
    Returns:
        Path to the created SQL file
    """
    # Get database URL from environment or use SQLite as fallback
    database_url = os.environ.get('DATABASE_URL')
    
    if not database_url:
        db_path = os.path.join('instance', 'printshop.db')
        database_url = f"sqlite:///{db_path}"
    
    # Create output filename if not provided
    if not output_file:
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f"printshop_export_{timestamp}.sql"
    
    # Connect to database
    engine = create_engine(database_url)
    metadata = MetaData()
    metadata.reflect(bind=engine)
    
    # Open output file
    with open(output_file, 'w') as f:
        # Write header
        f.write("-- Print Shop Management System Database Export\n")
        f.write(f"-- Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # Process each table
        for table_name in metadata.tables:
            table = Table(table_name, metadata, autoload_with=engine)
            
            # Skip SQLite internal tables
            if table_name.startswith('sqlite_'):
                continue
            
            f.write(f"-- Table: {table_name}\n")
            
            # Generate create table statement
            create_stmt = str(table.compile(dialect=engine.dialect).create_table())
            f.write(f"{create_stmt};\n\n")
            
            # Export data
            f.write(f"-- Data for table: {table_name}\n")
            
            # Get column names
            columns = [column.name for column in table.columns]
            
            # Select all rows
            with engine.connect() as conn:
                result = conn.execute(select(table))
                for row in result:
                    values = []
                    for column, value in zip(columns, row):
                        if value is None:
                            values.append("NULL")
                        elif isinstance(value, (int, float)):
                            values.append(str(value))
                        else:
                            # Escape single quotes
                            value_str = str(value).replace("'", "''")
                            values.append(f"'{value_str}'")
                    
                    # Write insert statement
                    f.write(f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({', '.join(values)});\n")
            
            f.write("\n")
    
    print(f"Database exported to {output_file}")
    return output_file

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Export database to SQL file')
    parser.add_argument('--output', '-o', help='Output file path')
    args = parser.parse_args()
    
    export_database(args.output)
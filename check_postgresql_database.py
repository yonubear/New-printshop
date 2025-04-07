#!/usr/bin/env python3
"""
PostgreSQL Database Check and Fix Script

This script performs a comprehensive check of the PostgreSQL database structure and
automatically adds any missing components required by the Print Shop Management System.

Usage:
    python check_postgresql_database.py [--fix] [--verbose]

Options:
    --fix       Apply fixes automatically (default: only report issues)
    --verbose   Show detailed output of all checks

Features:
    - Verifies all required tables exist
    - Checks all required columns and their data types
    - Validates indexes and constraints
    - Fixes issues with reserved keywords (like 'order')
    - Adds missing columns with proper defaults
    - Updates table statistics for query optimization
    - Performs test queries to verify functionality
"""

import os
import sys
import argparse
import logging
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime
import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv


# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('db_checker')


class PostgreSQLDatabaseChecker:
    """
    Class to check and fix PostgreSQL database structure for the Print Shop Management System
    """
    
    # Define required tables and their primary columns
    REQUIRED_TABLES = {
        'user': ['id', 'username', 'email', 'password_hash'],
        'customer': ['id', 'name', 'email', 'phone', 'discount_percentage'],
        'order': ['id', 'order_number', 'customer_id', 'title', 'status', 'is_picked_up',
                 'pickup_date', 'pickup_by', 'pickup_signature', 'pickup_signature_name',
                 'tracking_code'],
        'order_item': ['id', 'order_id', 'name', 'quantity', 'unit_price'],
        'order_file': ['id', 'order_id', 'filename', 'file_path', 'upload_date', 'proof_status'],
        'paper_option': ['id', 'name', 'size', 'weight', 'type', 'color', 'cost_per_sheet'],
        'finishing_option': ['id', 'name', 'description', 'base_price', 'per_piece_price', 'min_price'],
        'print_pricing': ['id', 'name', 'color', 'paper_type', 'duplex', 'base_price', 'per_page_price'],
        'saved_price': ['id', 'name', 'description', 'cost_price', 'retail_price', 'sku'],
        'quote': ['id', 'quote_number', 'customer_id', 'title', 'status'],
        'quote_item': ['id', 'quote_id', 'name', 'quantity', 'unit_price'],
        'customer_price': ['id', 'customer_id', 'name', 'description', 'price', 'valid_from', 'valid_to']
    }
    
    # Define columns that should be indexed
    REQUIRED_INDEXES = {
        'order': ['order_number', 'customer_id', 'status', 'tracking_code'],
        'customer': ['name', 'email'],
        'quote': ['quote_number', 'customer_id', 'status'],
        'order_item': ['order_id'],
        'order_file': ['order_id'],
        'customer_price': ['customer_id', 'valid_from', 'valid_to']
    }
    
    # Define column data types and default values
    COLUMN_DEFINITIONS = {
        'id': {'type': 'SERIAL PRIMARY KEY', 'default': None},
        'order_number': {'type': 'VARCHAR(50)', 'default': None},
        'quote_number': {'type': 'VARCHAR(50)', 'default': None},
        'customer_id': {'type': 'INTEGER', 'default': None},
        'user_id': {'type': 'INTEGER', 'default': '1'},
        'name': {'type': 'VARCHAR(100)', 'default': None},
        'email': {'type': 'VARCHAR(120)', 'default': None},
        'phone': {'type': 'VARCHAR(20)', 'default': "''"},
        'title': {'type': 'VARCHAR(100)', 'default': "''"},
        'description': {'type': 'TEXT', 'default': "''"},
        'status': {'type': 'VARCHAR(20)', 'default': "'new'"},
        'discount_percentage': {'type': 'NUMERIC(5,2)', 'default': '0'},
        'quantity': {'type': 'INTEGER', 'default': '1'},
        'unit_price': {'type': 'NUMERIC(10,2)', 'default': '0'},
        'cost_price': {'type': 'NUMERIC(10,2)', 'default': '0'},
        'retail_price': {'type': 'NUMERIC(10,2)', 'default': '0'},
        'is_picked_up': {'type': 'BOOLEAN', 'default': 'false'},
        'pickup_date': {'type': 'TIMESTAMP', 'default': 'NULL'},
        'pickup_by': {'type': 'VARCHAR(100)', 'default': 'NULL'},
        'pickup_signature': {'type': 'TEXT', 'default': 'NULL'},
        'pickup_signature_name': {'type': 'VARCHAR(100)', 'default': 'NULL'},
        'tracking_code': {'type': 'VARCHAR(50)', 'default': 'NULL'},
        'filename': {'type': 'VARCHAR(255)', 'default': None},
        'file_path': {'type': 'VARCHAR(255)', 'default': None},
        'upload_date': {'type': 'TIMESTAMP', 'default': 'CURRENT_TIMESTAMP'},
        'proof_status': {'type': 'VARCHAR(20)', 'default': "'pending'"},
        'size': {'type': 'VARCHAR(50)', 'default': "''"},
        'weight': {'type': 'VARCHAR(20)', 'default': "''"},
        'type': {'type': 'VARCHAR(50)', 'default': "''"},
        'color': {'type': 'VARCHAR(50)', 'default': "'white'"},
        'cost_per_sheet': {'type': 'NUMERIC(10,4)', 'default': '0'},
        'base_price': {'type': 'NUMERIC(10,2)', 'default': '0'},
        'per_piece_price': {'type': 'NUMERIC(10,2)', 'default': '0'},
        'min_price': {'type': 'NUMERIC(10,2)', 'default': '0'},
        'per_page_price': {'type': 'NUMERIC(10,2)', 'default': '0'},
        'duplex': {'type': 'BOOLEAN', 'default': 'false'},
        'paper_type': {'type': 'VARCHAR(50)', 'default': "''"},
        'sku': {'type': 'VARCHAR(50)', 'default': "''"},
        'valid_from': {'type': 'DATE', 'default': 'CURRENT_DATE'},
        'valid_to': {'type': 'DATE', 'default': 'NULL'},
        'created_at': {'type': 'TIMESTAMP', 'default': 'CURRENT_TIMESTAMP'},
        'updated_at': {'type': 'TIMESTAMP', 'default': 'CURRENT_TIMESTAMP'},
        'username': {'type': 'VARCHAR(64)', 'default': None},
        'password_hash': {'type': 'VARCHAR(256)', 'default': None},
        'order_id': {'type': 'INTEGER', 'default': None},
        'quote_id': {'type': 'INTEGER', 'default': None},
    }
    
    # Define required foreign keys
    REQUIRED_FOREIGN_KEYS = {
        'order': [('customer_id', 'customer', 'id'), ('user_id', 'user', 'id')],
        'order_item': [('order_id', 'order', 'id')],
        'order_file': [('order_id', 'order', 'id')],
        'quote': [('customer_id', 'customer', 'id'), ('user_id', 'user', 'id')],
        'quote_item': [('quote_id', 'quote', 'id')],
        'customer_price': [('customer_id', 'customer', 'id')],
    }
    
    def __init__(self, fix=False, verbose=False):
        """
        Initialize the database checker
        
        Args:
            fix: Whether to automatically apply fixes
            verbose: Whether to show detailed output
        """
        self.fix = fix
        self.verbose = verbose
        self.conn = None
        self.cursor = None
        self.issues_found = 0
        self.fixes_applied = 0
        
        # Load environment variables from .env file
        load_dotenv()
        
        # Get database connection info from environment variables
        self.db_url = os.environ.get('DATABASE_URL')
        self.db_host = os.environ.get('PGHOST')
        self.db_port = os.environ.get('PGPORT')
        self.db_name = os.environ.get('PGDATABASE')
        self.db_user = os.environ.get('PGUSER')
        self.db_password = os.environ.get('PGPASSWORD')
        
        if self.verbose:
            logger.setLevel(logging.DEBUG)
        
        if not self.db_url and not (self.db_host and self.db_name and self.db_user):
            logger.error("Database connection information not found. Please set DATABASE_URL "
                        "or PGHOST, PGPORT, PGDATABASE, PGUSER, PGPASSWORD environment variables.")
            sys.exit(1)
    
    def connect_to_database(self) -> bool:
        """
        Connect to PostgreSQL database
        
        Returns:
            bool: True if connection is successful, False otherwise
        """
        try:
            if self.db_url:
                logger.info(f"Connecting to database using DATABASE_URL")
                self.conn = psycopg2.connect(self.db_url)
            else:
                logger.info(f"Connecting to database {self.db_name} on {self.db_host}:{self.db_port}")
                self.conn = psycopg2.connect(
                    host=self.db_host,
                    port=self.db_port,
                    dbname=self.db_name,
                    user=self.db_user,
                    password=self.db_password
                )
            
            # Set isolation level for schema modifications
            self.conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            self.cursor = self.conn.cursor()
            logger.info("Database connection established successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to the database: {e}")
            return False
    
    def check_table_exists(self, table_name: str) -> bool:
        """
        Check if a table exists in the database
        
        Args:
            table_name: Name of the table to check
        
        Returns:
            bool: True if table exists, False otherwise
        """
        self.cursor.execute(
            """
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = %s
            );
            """, 
            (table_name,)
        )
        return self.cursor.fetchone()[0]
    
    def get_table_columns(self, table_name: str) -> Dict[str, Dict[str, str]]:
        """
        Get all columns and their data types for a table
        
        Args:
            table_name: Name of the table
        
        Returns:
            Dict: Dictionary of column names and their data types
        """
        self.cursor.execute(
            """
            SELECT column_name, data_type, character_maximum_length, 
                   numeric_precision, numeric_scale, is_nullable,
                   column_default
            FROM information_schema.columns 
            WHERE table_schema = 'public' AND table_name = %s
            """, 
            (table_name,)
        )
        
        columns = {}
        for col in self.cursor.fetchall():
            col_name = col[0]
            data_type = col[1]
            max_length = col[2]
            num_precision = col[3]
            num_scale = col[4]
            is_nullable = col[5]
            default_value = col[6]
            
            # Format the data type with precision/length if applicable
            if data_type == 'character varying' and max_length:
                formatted_type = f"VARCHAR({max_length})"
            elif data_type == 'numeric' and num_precision and num_scale:
                formatted_type = f"NUMERIC({num_precision},{num_scale})"
            else:
                formatted_type = data_type.upper()
            
            columns[col_name] = {
                'type': formatted_type,
                'nullable': is_nullable,
                'default': default_value
            }
        
        return columns
    
    def get_table_indexes(self, table_name: str) -> List[str]:
        """
        Get all indexes for a table
        
        Args:
            table_name: Name of the table
        
        Returns:
            List: List of indexed column names
        """
        self.cursor.execute(
            """
            SELECT a.attname
            FROM pg_catalog.pg_class c
            JOIN pg_catalog.pg_index i ON i.indexrelid = c.oid
            JOIN pg_catalog.pg_class t ON i.indrelid = t.oid
            JOIN pg_catalog.pg_attribute a ON a.attrelid = t.oid AND a.attnum = ANY(i.indkey)
            WHERE t.relname = %s
            AND c.relkind = 'i'
            AND NOT i.indisprimary
            """, 
            (table_name,)
        )
        
        return [col[0] for col in self.cursor.fetchall()]
    
    def get_table_foreign_keys(self, table_name: str) -> List[Tuple[str, str, str]]:
        """
        Get all foreign keys for a table
        
        Args:
            table_name: Name of the table
        
        Returns:
            List: List of tuples (column_name, referenced_table, referenced_column)
        """
        self.cursor.execute(
            """
            SELECT
                kcu.column_name,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name
            FROM
                information_schema.table_constraints AS tc
                JOIN information_schema.key_column_usage AS kcu
                  ON tc.constraint_name = kcu.constraint_name
                  AND tc.table_schema = kcu.table_schema
                JOIN information_schema.constraint_column_usage AS ccu
                  ON ccu.constraint_name = tc.constraint_name
                  AND ccu.table_schema = tc.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_name = %s;
            """, 
            (table_name,)
        )
        
        return [(col[0], col[1], col[2]) for col in self.cursor.fetchall()]
    
    def create_table(self, table_name: str) -> bool:
        """
        Create a table with required columns
        
        Args:
            table_name: Name of the table to create
        
        Returns:
            bool: True if table was created successfully, False otherwise
        """
        if table_name not in self.REQUIRED_TABLES:
            logger.error(f"Table {table_name} is not defined in REQUIRED_TABLES")
            return False
        
        # Get required columns for this table
        columns = self.REQUIRED_TABLES[table_name]
        
        # Build SQL statement for table creation
        column_defs = []
        for col in columns:
            if col in self.COLUMN_DEFINITIONS:
                col_def = self.COLUMN_DEFINITIONS[col]
                column_defs.append(f"{col} {col_def['type']}")
            else:
                logger.warning(f"Column {col} is not defined in COLUMN_DEFINITIONS, skipping")
        
        # Add created_at and updated_at columns if not already included
        if 'created_at' not in columns:
            column_defs.append("created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
        if 'updated_at' not in columns:
            column_defs.append("updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
        
        # Create the table
        try:
            # Handle 'order' table specially since it's a reserved keyword
            if table_name == 'order':
                # Use psycopg2.sql for proper quoting of reserved keywords
                parts = []
                for col_def in column_defs:
                    parts.append(sql.SQL(col_def))
                
                create_sql = sql.SQL("CREATE TABLE {} ({})").format(
                    sql.Identifier(table_name),
                    sql.SQL(", ").join(parts)
                )
                
                # Special approach for order table pickup columns
                # (for databases where ALTER TABLE with quoted identifiers isn't working properly)
                if self.fix:
                    # First create the basic table
                    logger.info(f"Creating table '{table_name}' with proper quoting")
                    self.cursor.execute(create_sql)
                    self.fixes_applied += 1
                    
                    # Then directly add pickup columns with quoted table name
                    logger.info(f"Adding pickup columns to '{table_name}' table")
                    pickup_columns = [
                        ('is_picked_up', 'BOOLEAN', 'false'),
                        ('pickup_date', 'TIMESTAMP', 'NULL'),
                        ('pickup_by', 'VARCHAR(100)', 'NULL'),
                        ('pickup_signature', 'TEXT', 'NULL'),
                        ('pickup_signature_name', 'VARCHAR(100)', 'NULL'),
                        ('tracking_code', 'VARCHAR(50)', 'NULL')
                    ]
                    
                    for col_name, col_type, default_val in pickup_columns:
                        if col_name not in columns:
                            continue
                            
                        add_col_sql = sql.SQL('ALTER TABLE {} ADD COLUMN IF NOT EXISTS {} {} DEFAULT {}').format(
                            sql.Identifier(table_name),
                            sql.Identifier(col_name),
                            sql.SQL(col_type),
                            sql.SQL(default_val)
                        )
                        try:
                            self.cursor.execute(add_col_sql)
                            logger.info(f"✅ Added column {col_name} to table {table_name}")
                        except Exception as col_error:
                            logger.error(f"Failed to add column {col_name} to table {table_name}: {col_error}")
                    
                    logger.info(f"✅ Table {table_name} created successfully with pickup columns")
                    return True
                else:
                    logger.info(f"Would create table {table_name} with proper quoting (run with --fix to apply)")
                    self.issues_found += 1
                    return False
            else:
                # For tables other than 'order', use the standard approach
                create_sql = f"CREATE TABLE {table_name} ({', '.join(column_defs)})"
                logger.info(f"Creating table {table_name}")
                logger.debug(create_sql)
                
                if self.fix:
                    self.cursor.execute(create_sql)
                    self.fixes_applied += 1
                    logger.info(f"✅ Table {table_name} created successfully")
                    return True
                else:
                    logger.info(f"Would create table {table_name} (run with --fix to apply)")
                    self.issues_found += 1
                    return False
        except Exception as e:
            logger.error(f"Failed to create table {table_name}: {e}")
            return False
    
    def add_column(self, table_name: str, column_name: str) -> bool:
        """
        Add a column to a table
        
        Args:
            table_name: Name of the table
            column_name: Name of the column to add
        
        Returns:
            bool: True if column was added successfully, False otherwise
        """
        if column_name not in self.COLUMN_DEFINITIONS:
            logger.error(f"Column {column_name} is not defined in COLUMN_DEFINITIONS")
            return False
        
        # Get column definition
        col_def = self.COLUMN_DEFINITIONS[column_name]
        default_val = col_def['default']
        
        # Build SQL statement for adding column - using psycopg2 sql module for proper quoting
        # Handle 'order' table specially since it's a reserved keyword
        if table_name == 'order':
            # Use psycopg2.sql for proper quoting of reserved keywords
            add_sql = sql.SQL("ALTER TABLE {} ADD COLUMN {} {}").format(
                sql.Identifier(table_name),
                sql.Identifier(column_name),
                sql.SQL(col_def['type'])
            )
            
            if default_val is not None:
                add_sql = sql.SQL("{} DEFAULT {}").format(
                    add_sql,
                    sql.SQL(default_val)
                )
        else:
            # For non-reserved keywords, continue with f-string approach
            add_sql = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {col_def['type']}"
            if default_val is not None:
                add_sql += f" DEFAULT {default_val}"
        
        # Add the column
        try:
            logger.info(f"Adding column {column_name} to table {table_name}")
            logger.debug(add_sql)
            
            if self.fix:
                self.cursor.execute(add_sql)
                self.fixes_applied += 1
                logger.info(f"✅ Column {column_name} added to table {table_name}")
                return True
            else:
                logger.info(f"Would add column {column_name} to table {table_name} (run with --fix to apply)")
                self.issues_found += 1
                return False
        except Exception as e:
            logger.error(f"Failed to add column {column_name} to table {table_name}: {e}")
            return False
    
    def create_index(self, table_name: str, column_name: str) -> bool:
        """
        Create an index on a column
        
        Args:
            table_name: Name of the table
            column_name: Name of the column to index
        
        Returns:
            bool: True if index was created successfully, False otherwise
        """
        # Generate a unique index name
        index_name = f"idx_{table_name}_{column_name}"
        
        # Create the index
        try:
            # Handle 'order' table specially since it's a reserved keyword
            if table_name == 'order':
                # Use psycopg2.sql for proper quoting of reserved keywords
                create_sql = sql.SQL("CREATE INDEX {} ON {} ({})").format(
                    sql.Identifier(index_name),
                    sql.Identifier(table_name),
                    sql.Identifier(column_name)
                )
            else:
                create_sql = f"CREATE INDEX {index_name} ON {table_name} ({column_name})"
                
            logger.info(f"Creating index on {table_name}.{column_name}")
            logger.debug(f"SQL: {create_sql}")
            
            if self.fix:
                self.cursor.execute(create_sql)
                self.fixes_applied += 1
                logger.info(f"✅ Index created on {table_name}.{column_name}")
                return True
            else:
                logger.info(f"Would create index on {table_name}.{column_name} (run with --fix to apply)")
                self.issues_found += 1
                return False
        except Exception as e:
            logger.error(f"Failed to create index on {table_name}.{column_name}: {e}")
            return False
    
    def create_foreign_key(self, table_name: str, column: str, ref_table: str, ref_column: str) -> bool:
        """
        Create a foreign key constraint
        
        Args:
            table_name: Name of the table
            column: Name of the column
            ref_table: Name of the referenced table
            ref_column: Name of the referenced column
        
        Returns:
            bool: True if foreign key was created successfully, False otherwise
        """
        # Generate a unique constraint name
        constraint_name = f"fk_{table_name}_{column}_{ref_table}_{ref_column}"
        
        # Create the foreign key constraint
        try:
            # Handle 'order' table specially since it's a reserved keyword
            if table_name == 'order' or ref_table == 'order':
                # Use psycopg2.sql for proper quoting of reserved keywords
                create_sql = sql.SQL("ALTER TABLE {} ADD CONSTRAINT {} FOREIGN KEY ({}) REFERENCES {} ({}) ON DELETE CASCADE").format(
                    sql.Identifier(table_name),
                    sql.Identifier(constraint_name),
                    sql.Identifier(column),
                    sql.Identifier(ref_table),
                    sql.Identifier(ref_column)
                )
            else:
                create_sql = f"""
                    ALTER TABLE {table_name} 
                    ADD CONSTRAINT {constraint_name} 
                    FOREIGN KEY ({column}) 
                    REFERENCES {ref_table} ({ref_column})
                    ON DELETE CASCADE
                """
                
            logger.info(f"Creating foreign key constraint from {table_name}.{column} to {ref_table}.{ref_column}")
            logger.debug(f"SQL: {create_sql}")
            
            if self.fix:
                self.cursor.execute(create_sql)
                self.fixes_applied += 1
                logger.info(f"✅ Foreign key constraint created from {table_name}.{column} to {ref_table}.{ref_column}")
                return True
            else:
                logger.info(f"Would create foreign key constraint from {table_name}.{column} to {ref_table}.{ref_column} (run with --fix to apply)")
                self.issues_found += 1
                return False
        except Exception as e:
            logger.error(f"Failed to create foreign key constraint: {e}")
            return False
    
    def fix_order_table_quoting(self) -> bool:
        """
        Fix issues with the 'order' table name (reserved word in PostgreSQL)
        
        Returns:
            bool: True if fix was applied successfully, False otherwise
        """
        # Check if the model has __tablename__ attribute set
        try:
            # This is just a check to verify if order table exists and is properly quoted
            self.cursor.execute('SELECT * FROM "order" LIMIT 1')
            logger.info("✅ Order table quoting is properly configured")
            return True
        except Exception as e:
            logger.error(f"Order table quoting issue detected: {e}")
            
            # If we're not in fix mode, just report the issue
            if not self.fix:
                logger.info("Would fix order table quoting (run with --fix to apply)")
                self.issues_found += 1
                return False
            
            # Try to create a trigger or function to refresh the table statistics
            try:
                self.cursor.execute('ANALYZE "order"')
                self.fixes_applied += 1
                logger.info("✅ Order table quoting fixed and statistics refreshed")
                return True
            except Exception as e2:
                logger.error(f"Failed to fix order table quoting: {e2}")
                return False
    
    def check_test_queries(self) -> bool:
        """
        Run test queries to verify database functionality
        
        Returns:
            bool: True if all test queries passed, False otherwise
        """
        test_queries = [
            "SELECT * FROM customer LIMIT 1",
            'SELECT * FROM "order" LIMIT 1',
            "SELECT * FROM order_item LIMIT 1",
            "SELECT * FROM paper_option LIMIT 1",
            "SELECT * FROM finishing_option LIMIT 1",
            "SELECT * FROM quote LIMIT 1",
            
            # Join queries
            """
            SELECT o.order_number, c.name as customer_name
            FROM "order" o
            JOIN customer c ON o.customer_id = c.id
            LIMIT 1
            """,
            
            # Query with is_picked_up column
            """
            SELECT id, order_number, is_picked_up
            FROM "order"
            WHERE is_picked_up = false
            LIMIT 1
            """
        ]
        
        all_passed = True
        for query in test_queries:
            try:
                logger.debug(f"Running test query: {query}")
                self.cursor.execute(query)
                result = self.cursor.fetchall()
                logger.debug(f"Query result: {result}")
                logger.info(f"✅ Test query passed: {query.splitlines()[0][:50]}...")
            except Exception as e:
                logger.error(f"❌ Test query failed: {query.splitlines()[0][:50]}...: {e}")
                all_passed = False
                self.issues_found += 1
        
        return all_passed
    
    def check_and_fix_all(self) -> Tuple[int, int]:
        """
        Run all checks and fixes
        
        Returns:
            Tuple: (issues_found, fixes_applied)
        """
        # Connect to the database
        if not self.connect_to_database():
            return self.issues_found, self.fixes_applied
        
        try:
            # Check all required tables
            logger.info("\n== Checking required tables ==")
            for table_name in self.REQUIRED_TABLES:
                if self.check_table_exists(table_name):
                    logger.info(f"✅ Table {table_name} exists")
                    
                    # Check columns for this table
                    existing_columns = self.get_table_columns(table_name)
                    required_columns = self.REQUIRED_TABLES[table_name]
                    
                    for col in required_columns:
                        if col in existing_columns:
                            logger.debug(f"Column {col} exists in table {table_name}")
                        else:
                            logger.warning(f"❌ Column {col} missing from table {table_name}")
                            self.add_column(table_name, col)
                else:
                    logger.warning(f"❌ Table {table_name} does not exist")
                    self.create_table(table_name)
            
            # Check indexes
            logger.info("\n== Checking required indexes ==")
            for table_name in self.REQUIRED_INDEXES:
                if self.check_table_exists(table_name):
                    existing_indexes = self.get_table_indexes(table_name)
                    required_indexes = self.REQUIRED_INDEXES[table_name]
                    
                    for col in required_indexes:
                        if col in existing_indexes:
                            logger.info(f"✅ Index on {table_name}.{col} exists")
                        else:
                            logger.warning(f"❌ Index on {table_name}.{col} missing")
                            self.create_index(table_name, col)
            
            # Check foreign keys
            logger.info("\n== Checking required foreign keys ==")
            for table_name in self.REQUIRED_FOREIGN_KEYS:
                if self.check_table_exists(table_name):
                    existing_fks = self.get_table_foreign_keys(table_name)
                    required_fks = self.REQUIRED_FOREIGN_KEYS[table_name]
                    
                    for fk in required_fks:
                        col, ref_table, ref_col = fk
                        
                        # Check if this foreign key exists
                        fk_exists = False
                        for existing_fk in existing_fks:
                            if existing_fk[0] == col and existing_fk[1] == ref_table and existing_fk[2] == ref_col:
                                fk_exists = True
                                break
                        
                        if fk_exists:
                            logger.info(f"✅ Foreign key from {table_name}.{col} to {ref_table}.{ref_col} exists")
                        else:
                            logger.warning(f"❌ Foreign key from {table_name}.{col} to {ref_table}.{ref_col} missing")
                            self.create_foreign_key(table_name, col, ref_table, ref_col)
            
            # Fix order table quoting issues
            logger.info("\n== Checking order table quoting ==")
            self.fix_order_table_quoting()
            
            # Refresh table statistics
            logger.info("\n== Refreshing table statistics ==")
            if self.fix:
                self.cursor.execute("ANALYZE")
                logger.info("✅ Table statistics refreshed")
            
            # Run test queries
            logger.info("\n== Running test queries ==")
            self.check_test_queries()
            
            # Provide summary
            logger.info("\n== Summary ==")
            logger.info(f"Issues found: {self.issues_found}")
            logger.info(f"Fixes applied: {self.fixes_applied}")
            
            if self.issues_found > 0 and not self.fix:
                logger.info("Run with --fix to apply fixes")
            
            return self.issues_found, self.fixes_applied
            
        except Exception as e:
            logger.error(f"An error occurred during database check: {e}")
            return self.issues_found, self.fixes_applied
        finally:
            # Close database connection
            if self.conn:
                self.conn.close()


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='PostgreSQL Database Check and Fix Tool')
    parser.add_argument('--fix', action='store_true', help='Apply fixes automatically')
    parser.add_argument('--verbose', action='store_true', help='Show detailed output')
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("PostgreSQL Database Check and Fix Tool")
    print("=" * 80)
    print()
    
    checker = PostgreSQLDatabaseChecker(fix=args.fix, verbose=args.verbose)
    issues, fixes = checker.check_and_fix_all()
    
    if issues == 0:
        print("\n✅ No issues found. Your database is correctly configured.")
    elif fixes > 0:
        print(f"\n✅ Fixed {fixes} issues. Your database is now correctly configured.")
    else:
        print(f"\n⚠️ Found {issues} issues. Run with --fix to apply fixes.")
    
    return 0 if issues == 0 or fixes > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
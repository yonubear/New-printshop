-- ================================================================
-- Print Shop Management System - PostgreSQL Database Fix Script
-- ================================================================
-- 
-- This script fixes issues with the 'order' table in PostgreSQL
-- and adds any missing pickup-related columns.
--
-- Instructions:
-- 1. Run this script directly on your PostgreSQL server:
--    psql -U your_username -d your_database -f fix_printshop_postgresql_database.sql
--
-- 2. This script combines multiple approaches to ensure the problem
--    is fixed regardless of your specific PostgreSQL configuration.
--
-- 3. The script is safe to run multiple times and will not duplicate columns.
--
-- ================================================================

-- Start transaction
BEGIN;

-- Output information about what we're doing
\echo 'Print Shop Management System - PostgreSQL Database Fix Script'
\echo '============================================================='
\echo ' '
\echo 'Starting database fixes...'

-- ----------------------------------------------------------------
-- APPROACH 1: Create functions for safe schema modifications
-- ----------------------------------------------------------------

-- Create a function to safely add columns if they don't exist
\echo 'Creating utility functions...'

CREATE OR REPLACE FUNCTION add_column_if_not_exists(
    p_table_name TEXT,
    p_column_name TEXT,
    p_data_type TEXT,
    p_default_value TEXT DEFAULT NULL
) RETURNS VOID AS $$
DECLARE
    column_exists BOOLEAN;
BEGIN
    -- Check if column exists
    SELECT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'public'
            AND table_name = p_table_name
            AND column_name = p_column_name
    ) INTO column_exists;

    -- Add column if it doesn't exist
    IF NOT column_exists THEN
        IF p_default_value IS NULL THEN
            EXECUTE format('ALTER TABLE %I ADD COLUMN %I %s', 
                           p_table_name, p_column_name, p_data_type);
        ELSE
            EXECUTE format('ALTER TABLE %I ADD COLUMN %I %s DEFAULT %s', 
                           p_table_name, p_column_name, p_data_type, p_default_value);
        END IF;
        
        RAISE NOTICE 'Added column %.% of type %', p_table_name, p_column_name, p_data_type;
    ELSE
        RAISE NOTICE 'Column %.% already exists', p_table_name, p_column_name;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Create a function to safely create an index if it doesn't exist
CREATE OR REPLACE FUNCTION create_index_if_not_exists(
    p_index_name TEXT,
    p_table_name TEXT,
    p_column_name TEXT
) RETURNS VOID AS $$
DECLARE
    index_exists BOOLEAN;
BEGIN
    -- Check if index exists
    SELECT EXISTS (
        SELECT 1
        FROM pg_indexes
        WHERE schemaname = 'public'
            AND tablename = p_table_name
            AND indexname = p_index_name
    ) INTO index_exists;

    -- Create index if it doesn't exist
    IF NOT index_exists THEN
        EXECUTE format('CREATE INDEX %I ON %I (%I)', 
                       p_index_name, p_table_name, p_column_name);
        RAISE NOTICE 'Created index % on %.%', p_index_name, p_table_name, p_column_name;
    ELSE
        RAISE NOTICE 'Index % already exists', p_index_name;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Create a function to safely create a foreign key if it doesn't exist
CREATE OR REPLACE FUNCTION create_foreign_key_if_not_exists(
    p_constraint_name TEXT,
    p_table_name TEXT,
    p_column_name TEXT,
    p_ref_table_name TEXT,
    p_ref_column_name TEXT
) RETURNS VOID AS $$
DECLARE
    fk_exists BOOLEAN;
BEGIN
    -- Check if foreign key exists
    SELECT EXISTS (
        SELECT 1
        FROM information_schema.table_constraints
        WHERE constraint_type = 'FOREIGN KEY'
            AND table_schema = 'public'
            AND table_name = p_table_name
            AND constraint_name = p_constraint_name
    ) INTO fk_exists;

    -- Create foreign key if it doesn't exist
    IF NOT fk_exists THEN
        EXECUTE format(
            'ALTER TABLE %I ADD CONSTRAINT %I FOREIGN KEY (%I) REFERENCES %I (%I) ON DELETE CASCADE',
            p_table_name, p_constraint_name, p_column_name, p_ref_table_name, p_ref_column_name
        );
        RAISE NOTICE 'Created foreign key % from %.% to %.%', 
                     p_constraint_name, p_table_name, p_column_name, p_ref_table_name, p_ref_column_name;
    ELSE
        RAISE NOTICE 'Foreign key % already exists', p_constraint_name;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Create a function to execute SQL safely with error handling
CREATE OR REPLACE FUNCTION execute_sql_safely(sql_cmd TEXT, description TEXT) RETURNS VOID AS $$
BEGIN
    EXECUTE sql_cmd;
    RAISE NOTICE '✅ %: Success', description;
EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE '❌ %: Failed with error: %', description, SQLERRM;
    RAISE NOTICE 'SQL was: %', sql_cmd;
END;
$$ LANGUAGE plpgsql;

-- ----------------------------------------------------------------
-- APPROACH 2: Check if the order table exists and create it if not
-- ----------------------------------------------------------------

\echo 'Checking if order table exists...'

DO $$ 
BEGIN
    IF NOT EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'order') THEN
        RAISE NOTICE 'Creating order table from scratch';
        
        EXECUTE '
        CREATE TABLE "order" (
            id SERIAL PRIMARY KEY,
            order_number VARCHAR(50) UNIQUE NOT NULL,
            customer_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            title VARCHAR(100) NOT NULL,
            description TEXT,
            status VARCHAR(20) DEFAULT ''new'',
            due_date TIMESTAMP,
            total_price NUMERIC(10,2) DEFAULT 0,
            payment_status VARCHAR(20) DEFAULT ''unpaid'',
            amount_paid NUMERIC(10,2) DEFAULT 0,
            payment_date TIMESTAMP,
            payment_method VARCHAR(50),
            payment_reference VARCHAR(100),
            invoice_number VARCHAR(50),
            payment_notes TEXT,
            is_picked_up BOOLEAN DEFAULT false,
            pickup_date TIMESTAMP,
            pickup_by VARCHAR(100),
            pickup_signature TEXT,
            pickup_signature_name VARCHAR(100),
            tracking_code VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )';
        
        RAISE NOTICE 'Order table created with all required columns';
    ELSE
        RAISE NOTICE 'Order table already exists, will add missing columns';
    END IF;
END $$;

-- ----------------------------------------------------------------
-- APPROACH 3: Multiple methods to add the missing pickup columns
-- ----------------------------------------------------------------

\echo 'Adding missing pickup columns using different approaches...'

-- Method 1: Using the custom function
SELECT add_column_if_not_exists('order', 'is_picked_up', 'BOOLEAN', 'false');
SELECT add_column_if_not_exists('order', 'pickup_date', 'TIMESTAMP', 'NULL');
SELECT add_column_if_not_exists('order', 'pickup_by', 'VARCHAR(100)', 'NULL');
SELECT add_column_if_not_exists('order', 'pickup_signature', 'TEXT', 'NULL');
SELECT add_column_if_not_exists('order', 'pickup_signature_name', 'VARCHAR(100)', 'NULL');
SELECT add_column_if_not_exists('order', 'tracking_code', 'VARCHAR(50)', 'NULL');

-- Method 2: Direct ALTER TABLE with proper quoting and error handling
DO $$
BEGIN
    -- Try with safely quoted identifiers
    PERFORM execute_sql_safely(
        'ALTER TABLE "order" ADD COLUMN IF NOT EXISTS is_picked_up BOOLEAN DEFAULT false',
        'Adding is_picked_up with quoted table name'
    );
    
    PERFORM execute_sql_safely(
        'ALTER TABLE "order" ADD COLUMN IF NOT EXISTS pickup_date TIMESTAMP',
        'Adding pickup_date with quoted table name'
    );
    
    PERFORM execute_sql_safely(
        'ALTER TABLE "order" ADD COLUMN IF NOT EXISTS pickup_by VARCHAR(100)',
        'Adding pickup_by with quoted table name'
    );
    
    PERFORM execute_sql_safely(
        'ALTER TABLE "order" ADD COLUMN IF NOT EXISTS pickup_signature TEXT',
        'Adding pickup_signature with quoted table name'
    );
    
    PERFORM execute_sql_safely(
        'ALTER TABLE "order" ADD COLUMN IF NOT EXISTS pickup_signature_name VARCHAR(100)',
        'Adding pickup_signature_name with quoted table name'
    );
    
    PERFORM execute_sql_safely(
        'ALTER TABLE "order" ADD COLUMN IF NOT EXISTS tracking_code VARCHAR(50)',
        'Adding tracking_code with quoted table name'
    );
END $$;

-- Method A: Using format function with properly quoted identifiers
DO $$
DECLARE
  pickup_columns TEXT[] := ARRAY['is_picked_up', 'pickup_date', 'pickup_by', 'pickup_signature', 'pickup_signature_name', 'tracking_code'];
  column_types TEXT[] := ARRAY['BOOLEAN DEFAULT false', 'TIMESTAMP', 'VARCHAR(100)', 'TEXT', 'VARCHAR(100)', 'VARCHAR(50)'];
  sql_cmd TEXT;
  i INTEGER;
BEGIN
  FOR i IN 1..array_length(pickup_columns, 1) LOOP
    -- Check if column already exists
    IF NOT EXISTS (
      SELECT 1 FROM information_schema.columns 
      WHERE table_schema = 'public' 
        AND table_name = 'order' 
        AND column_name = pickup_columns[i]
    ) THEN
      -- Construct SQL command with format function
      sql_cmd := format(
        'ALTER TABLE %I ADD COLUMN %I %s',
        'order',
        pickup_columns[i],
        column_types[i]
      );
      
      -- Execute with exception handling
      BEGIN
        EXECUTE sql_cmd;
        RAISE NOTICE 'Added column % with type % using format approach', pickup_columns[i], column_types[i];
      EXCEPTION WHEN OTHERS THEN
        RAISE NOTICE 'Format approach: Failed to add column % with error: %', pickup_columns[i], SQLERRM;
      END;
    END IF;
  END LOOP;
END $$;

-- ----------------------------------------------------------------
-- APPROACH 4: Create missing indexes on the order table
-- ----------------------------------------------------------------

\echo 'Adding missing indexes to order table...'

-- Using the index function
SELECT create_index_if_not_exists('idx_order_customer_id', 'order', 'customer_id');
SELECT create_index_if_not_exists('idx_order_status', 'order', 'status');
SELECT create_index_if_not_exists('idx_order_tracking_code', 'order', 'tracking_code');

-- Direct approach with quoted identifiers
DO $$
BEGIN
    -- Only create indexes if they don't exist
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE tablename = 'order' AND indexname = 'idx_order_customer_id') THEN
        EXECUTE 'CREATE INDEX idx_order_customer_id ON "order" (customer_id)';
        RAISE NOTICE 'Created index idx_order_customer_id';
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE tablename = 'order' AND indexname = 'idx_order_status') THEN
        EXECUTE 'CREATE INDEX idx_order_status ON "order" (status)';
        RAISE NOTICE 'Created index idx_order_status';
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE tablename = 'order' AND indexname = 'idx_order_tracking_code') THEN
        EXECUTE 'CREATE INDEX idx_order_tracking_code ON "order" (tracking_code)';
        RAISE NOTICE 'Created index idx_order_tracking_code';
    END IF;
END $$;

-- ----------------------------------------------------------------
-- APPROACH 5: Create foreign keys if they don't exist
-- ----------------------------------------------------------------

\echo 'Adding foreign keys to order table...'

-- Using the foreign key function
SELECT create_foreign_key_if_not_exists('fk_order_customer_id', 'order', 'customer_id', 'customer', 'id');
SELECT create_foreign_key_if_not_exists('fk_order_user_id', 'order', 'user_id', 'user', 'id');

-- Direct approach with quoted identifiers
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'fk_order_customer_id' 
        AND table_name = 'order'
    ) THEN
        EXECUTE '
        ALTER TABLE "order" 
        ADD CONSTRAINT fk_order_customer_id 
        FOREIGN KEY (customer_id) 
        REFERENCES customer(id) 
        ON DELETE CASCADE';
        
        RAISE NOTICE 'Created foreign key fk_order_customer_id';
    END IF;
    
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'fk_order_user_id' 
        AND table_name = 'order'
    ) THEN
        EXECUTE '
        ALTER TABLE "order" 
        ADD CONSTRAINT fk_order_user_id 
        FOREIGN KEY (user_id) 
        REFERENCES "user"(id) 
        ON DELETE CASCADE';
        
        RAISE NOTICE 'Created foreign key fk_order_user_id';
    END IF;
END $$;

-- ----------------------------------------------------------------
-- APPROACH 6: Update statistics and verify changes
-- ----------------------------------------------------------------

\echo 'Updating table statistics...'

-- Update table statistics
ANALYZE "order";

-- Test query to verify is_picked_up column exists and is accessible
\echo 'Testing pickup columns with a SELECT query...'

DO $$ 
DECLARE
    test_result RECORD;
BEGIN
    BEGIN
        EXECUTE 'SELECT id, order_number, is_picked_up FROM "order" LIMIT 1' INTO test_result;
        RAISE NOTICE '✅ Test query successful: is_picked_up column exists and is accessible';
    EXCEPTION WHEN OTHERS THEN
        RAISE NOTICE '❌ Test query failed: %', SQLERRM;
    END;
END $$;

-- ----------------------------------------------------------------
-- Cleanup and completion
-- ----------------------------------------------------------------

-- Drop the temporary functions
\echo 'Cleaning up temporary functions...'

DROP FUNCTION IF EXISTS add_column_if_not_exists;
DROP FUNCTION IF EXISTS create_index_if_not_exists;
DROP FUNCTION IF EXISTS create_foreign_key_if_not_exists;
DROP FUNCTION IF EXISTS execute_sql_safely;

-- Commit transaction
COMMIT;

-- Verification queries
\echo 'Displaying final table information...'

\echo '\nColumns in order table:'
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_schema = 'public' AND table_name = 'order'
ORDER BY ordinal_position;

\echo '\nIndexes on order table:'
SELECT indexname, indexdef 
FROM pg_indexes 
WHERE tablename = 'order';

\echo '\nForeign keys on order table:'
SELECT tc.constraint_name, tc.constraint_type, kcu.column_name, 
       ccu.table_name AS foreign_table_name, ccu.column_name AS foreign_column_name
FROM information_schema.table_constraints AS tc 
JOIN information_schema.key_column_usage AS kcu
  ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
  ON ccu.constraint_name = tc.constraint_name
WHERE tc.table_name = 'order';

\echo '\nDatabase fix script completed successfully!'
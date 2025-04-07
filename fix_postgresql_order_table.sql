-- PostgreSQL Fix Script for Print Shop Management System
-- This script fixes issues with the 'order' table and adds missing pickup columns
-- Execute this script directly on your PostgreSQL database server

-- Start transaction
BEGIN;

-- Check if 'order' table exists and create it if missing
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'order') THEN
        CREATE TABLE "order" (
            id SERIAL PRIMARY KEY,
            order_number VARCHAR(50) UNIQUE NOT NULL,
            customer_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            title VARCHAR(100) NOT NULL,
            description TEXT,
            status VARCHAR(20) DEFAULT 'new',
            due_date TIMESTAMP,
            total_price NUMERIC(10,2) DEFAULT 0,
            payment_status VARCHAR(20) DEFAULT 'unpaid',
            amount_paid NUMERIC(10,2) DEFAULT 0,
            payment_date TIMESTAMP,
            payment_method VARCHAR(50),
            payment_reference VARCHAR(100),
            invoice_number VARCHAR(50),
            payment_notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    END IF;
END $$;

-- Function to safely add columns if they don't exist
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

-- Add missing pickup columns to 'order' table
SELECT add_column_if_not_exists('order', 'is_picked_up', 'BOOLEAN', 'false');
SELECT add_column_if_not_exists('order', 'pickup_date', 'TIMESTAMP', 'NULL');
SELECT add_column_if_not_exists('order', 'pickup_by', 'VARCHAR(100)', 'NULL');
SELECT add_column_if_not_exists('order', 'pickup_signature', 'TEXT', 'NULL');
SELECT add_column_if_not_exists('order', 'pickup_signature_name', 'VARCHAR(100)', 'NULL');
SELECT add_column_if_not_exists('order', 'tracking_code', 'VARCHAR(50)', 'NULL');

-- Create missing indexes on 'order' table
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE tablename = 'order' AND indexname = 'idx_order_customer_id') THEN
        CREATE INDEX idx_order_customer_id ON "order" (customer_id);
        RAISE NOTICE 'Created index idx_order_customer_id';
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE tablename = 'order' AND indexname = 'idx_order_status') THEN
        CREATE INDEX idx_order_status ON "order" (status);
        RAISE NOTICE 'Created index idx_order_status';
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE tablename = 'order' AND indexname = 'idx_order_tracking_code') THEN
        CREATE INDEX idx_order_tracking_code ON "order" (tracking_code);
        RAISE NOTICE 'Created index idx_order_tracking_code';
    END IF;
END $$;

-- Create foreign keys if they don't exist
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'fk_order_customer_id' 
        AND table_name = 'order'
    ) THEN
        ALTER TABLE "order" 
        ADD CONSTRAINT fk_order_customer_id 
        FOREIGN KEY (customer_id) 
        REFERENCES customer(id) 
        ON DELETE CASCADE;
        
        RAISE NOTICE 'Created foreign key fk_order_customer_id';
    END IF;
    
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'fk_order_user_id' 
        AND table_name = 'order'
    ) THEN
        ALTER TABLE "order" 
        ADD CONSTRAINT fk_order_user_id 
        FOREIGN KEY (user_id) 
        REFERENCES "user"(id) 
        ON DELETE CASCADE;
        
        RAISE NOTICE 'Created foreign key fk_order_user_id';
    END IF;
END $$;

-- Update table statistics
ANALYZE "order";

-- Test query to verify is_picked_up column exists and is accessible
DO $$ 
DECLARE
    test_result RECORD;
BEGIN
    BEGIN
        EXECUTE 'SELECT id, order_number, is_picked_up FROM "order" LIMIT 1' INTO test_result;
        RAISE NOTICE 'Test query successful: is_picked_up column exists and is accessible';
    EXCEPTION WHEN OTHERS THEN
        RAISE EXCEPTION 'Test query failed: %', SQLERRM;
    END;
END $$;

-- Commit transaction
COMMIT;

-- Drop the temporary function
DROP FUNCTION IF EXISTS add_column_if_not_exists;

-- Verification queries
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_schema = 'public' AND table_name = 'order'
ORDER BY ordinal_position;

SELECT indexname, indexdef 
FROM pg_indexes 
WHERE tablename = 'order';

SELECT tc.constraint_name, tc.constraint_type, kcu.column_name, 
       ccu.table_name AS foreign_table_name, ccu.column_name AS foreign_column_name
FROM information_schema.table_constraints AS tc 
JOIN information_schema.key_column_usage AS kcu
  ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
  ON ccu.constraint_name = tc.constraint_name
WHERE tc.table_name = 'order';
-- Emergency Order Table Pickup Column Fix
-- This script uses alternative methods to add the required columns
-- to the 'order' table in PostgreSQL

-- Start transaction
BEGIN;

-- Function to execute dynamic SQL with properly quoted identifiers
CREATE OR REPLACE FUNCTION execute_sql(sql_text TEXT) RETURNS VOID AS $$
BEGIN
    EXECUTE sql_text;
EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE 'Error executing SQL: %', SQLERRM;
    RAISE NOTICE 'SQL was: %', sql_text;
END;
$$ LANGUAGE plpgsql;

-- Add pickup columns with several different techniques
SELECT execute_sql('ALTER TABLE "order" ADD COLUMN IF NOT EXISTS is_picked_up BOOLEAN DEFAULT false');
SELECT execute_sql('ALTER TABLE "order" ADD COLUMN IF NOT EXISTS pickup_date TIMESTAMP');
SELECT execute_sql('ALTER TABLE "order" ADD COLUMN IF NOT EXISTS pickup_by VARCHAR(100)');
SELECT execute_sql('ALTER TABLE "order" ADD COLUMN IF NOT EXISTS pickup_signature TEXT');
SELECT execute_sql('ALTER TABLE "order" ADD COLUMN IF NOT EXISTS pickup_signature_name VARCHAR(100)');
SELECT execute_sql('ALTER TABLE "order" ADD COLUMN IF NOT EXISTS tracking_code VARCHAR(50)');

-- Alternative approach using quoted identifiers
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
      -- Construct SQL command with explicit quoting
      sql_cmd := 'ALTER TABLE "order" ADD COLUMN "' || pickup_columns[i] || '" ' || column_types[i];
      
      -- Execute with exception handling
      BEGIN
        EXECUTE sql_cmd;
        RAISE NOTICE 'Added column % with type %', pickup_columns[i], column_types[i];
      EXCEPTION WHEN OTHERS THEN
        RAISE NOTICE 'Failed to add column % with error: %', pickup_columns[i], SQLERRM;
      END;
    ELSE
      RAISE NOTICE 'Column % already exists', pickup_columns[i];
    END IF;
  END LOOP;
END $$;

-- Drop the function
DROP FUNCTION IF EXISTS execute_sql;

-- Update table statistics
ANALYZE "order";

-- Commit transaction
COMMIT;

-- Verify columns exist
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_schema = 'public' AND table_name = 'order'
AND column_name IN ('is_picked_up', 'pickup_date', 'pickup_by', 'pickup_signature', 'pickup_signature_name', 'tracking_code')
ORDER BY column_name;
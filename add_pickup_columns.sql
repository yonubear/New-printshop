-- Direct fix for adding pickup columns to order table
-- This is a simplified script that focuses only on adding the missing columns
-- Execute this script directly on your PostgreSQL database

-- Start transaction
BEGIN;

-- Directly add pickup columns with proper quoting of the 'order' table name
ALTER TABLE "order" ADD COLUMN IF NOT EXISTS is_picked_up BOOLEAN DEFAULT false;
ALTER TABLE "order" ADD COLUMN IF NOT EXISTS pickup_date TIMESTAMP DEFAULT NULL;
ALTER TABLE "order" ADD COLUMN IF NOT EXISTS pickup_by VARCHAR(100) DEFAULT NULL;
ALTER TABLE "order" ADD COLUMN IF NOT EXISTS pickup_signature TEXT DEFAULT NULL;
ALTER TABLE "order" ADD COLUMN IF NOT EXISTS pickup_signature_name VARCHAR(100) DEFAULT NULL;
ALTER TABLE "order" ADD COLUMN IF NOT EXISTS tracking_code VARCHAR(50) DEFAULT NULL;

-- Create missing indexes with proper quoting
CREATE INDEX IF NOT EXISTS idx_order_customer_id ON "order" (customer_id);
CREATE INDEX IF NOT EXISTS idx_order_status ON "order" (status);
CREATE INDEX IF NOT EXISTS idx_order_tracking_code ON "order" (tracking_code);

-- Update table statistics
ANALYZE "order";

-- Commit transaction
COMMIT;

-- Verify columns were added
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_schema = 'public' AND table_name = 'order'
AND column_name IN ('is_picked_up', 'pickup_date', 'pickup_by', 'pickup_signature', 'pickup_signature_name', 'tracking_code')
ORDER BY ordinal_position;
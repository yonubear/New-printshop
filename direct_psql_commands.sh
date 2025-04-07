#!/bin/bash
# Direct PSQL Commands to fix the pickup columns
# Run this script directly passing your database connection parameters
# Example: ./direct_psql_commands.sh "host=localhost port=5432 user=postgres password=yourpassword dbname=printshop"

# Check if connection string parameter is provided
if [ -z "$1" ]; then
  echo "Usage: $0 \"connection_string\""
  echo "Example: $0 \"host=localhost port=5432 user=postgres password=yourpassword dbname=printshop\""
  exit 1
fi

CONNECTION_STRING="$1"

# Function to run SQL and report results
run_sql() {
  local sql="$1"
  local description="$2"
  
  echo "Executing: $description"
  psql "$CONNECTION_STRING" -c "$sql"
  if [ $? -eq 0 ]; then
    echo "✅ Success: $description"
  else
    echo "❌ Failed: $description"
  fi
  echo "-------------------------------------"
}

# Add is_picked_up column
run_sql "ALTER TABLE \"order\" ADD COLUMN IF NOT EXISTS is_picked_up BOOLEAN DEFAULT false;" \
        "Adding is_picked_up column"

# Add pickup_date column
run_sql "ALTER TABLE \"order\" ADD COLUMN IF NOT EXISTS pickup_date TIMESTAMP;" \
        "Adding pickup_date column"

# Add pickup_by column
run_sql "ALTER TABLE \"order\" ADD COLUMN IF NOT EXISTS pickup_by VARCHAR(100);" \
        "Adding pickup_by column"

# Add pickup_signature column
run_sql "ALTER TABLE \"order\" ADD COLUMN IF NOT EXISTS pickup_signature TEXT;" \
        "Adding pickup_signature column"

# Add pickup_signature_name column
run_sql "ALTER TABLE \"order\" ADD COLUMN IF NOT EXISTS pickup_signature_name VARCHAR(100);" \
        "Adding pickup_signature_name column"

# Add tracking_code column
run_sql "ALTER TABLE \"order\" ADD COLUMN IF NOT EXISTS tracking_code VARCHAR(50);" \
        "Adding tracking_code column"

# Add necessary indexes
run_sql "CREATE INDEX IF NOT EXISTS idx_order_customer_id ON \"order\" (customer_id);" \
        "Creating index on customer_id"

run_sql "CREATE INDEX IF NOT EXISTS idx_order_status ON \"order\" (status);" \
        "Creating index on status"

run_sql "CREATE INDEX IF NOT EXISTS idx_order_tracking_code ON \"order\" (tracking_code);" \
        "Creating index on tracking_code"

# Update statistics
run_sql "ANALYZE \"order\";" \
        "Updating table statistics"

# Verify columns
run_sql "SELECT column_name, data_type, is_nullable FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'order' AND column_name IN ('is_picked_up', 'pickup_date', 'pickup_by', 'pickup_signature', 'pickup_signature_name', 'tracking_code') ORDER BY column_name;" \
        "Verifying columns"

echo "Database update completed."
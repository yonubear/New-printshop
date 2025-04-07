# PrintShop v5.0.6 Database Upgrade Guide

This guide provides detailed instructions for upgrading your PrintShop database to version 5.0.6 using the new one-step database upgrade script.

## Overview

PrintShop v5.0.6 includes several important database schema changes:

1. Addition of the `quote_item_material` table for better material tracking
2. Addition of the `n_up` column to the `quote_item` table
3. Addition of the `self_cover` column to the `quote_item` table
4. Addition of the `quote_id` column to the `order` table for quote-to-order conversion

The new `update_v506_single_step.py` script performs all these migrations automatically in a single step.

## Prerequisites

- PostgreSQL database set up with PrintShop v5.0.0 or later
- Python 3.6+ installed
- Required Python packages:
  - python-dotenv (recommended, but optional)
  - psycopg2

## Backup First!

**IMPORTANT**: Always back up your database before performing any migrations. The upgrade script will attempt to create a backup if `pg_dump` is available, but manual backups are still recommended.

To manually back up your database, use:

```bash
pg_dump -h <host> -p <port> -U <username> -d <database> -f printshop_backup_$(date +%Y%m%d_%H%M%S).sql
```

## Simple Method: One-Step Upgrade

### Step 1: Extract the Upgrade Package

Extract the `printshop_v5.0.6_xxxxxxxx.zip` file to your PrintShop installation directory.

### Step 2: Run the One-Step Upgrade Script

```bash
python update_v506_single_step.py
```

This script will:
1. Check your environment variables
2. Create a database backup (if pg_dump is available)
3. Run all required migrations in a single transaction
4. Back up your code files before replacing them
5. Log all operations to a timestamped log file

### Step 3: Restart Your Application

After the upgrade completes, restart your application to apply the changes:

```bash
# If using Gunicorn
sudo systemctl restart printshop

# If using direct Python
python main.py
```

## Verifying the Upgrade

After the upgrade is complete, verify that:

1. You can add materials to quote items
2. The N-up printing feature works for quotes
3. You can convert quotes to orders successfully

## Troubleshooting

If you encounter any issues during the upgrade:

1. Check the log file created in your PrintShop directory (format: `v506_upgrade_yyyymmdd_hhmmss.log`)
2. Restore your backup if necessary
3. Run the script with additional logging:
   ```bash
   python -m pdb update_v506_single_step.py
   ```

## Manual Migration (If Needed)

If the automatic upgrade fails, you can perform each migration step manually:

1. Create the quote_item_material table:
   ```bash
   python add_quote_item_material_table.py
   ```

2. Add the n-up column:
   ```bash
   python add_quote_item_nup_column.py
   ```

3. Update the application files manually by copying them from the package.

## Testing the Upgrade Script

For advanced users, you can test the upgrade script before running it on your production database:

```bash
python test_v506_upgrade.py
```

This script creates a temporary environment and tests the upgrade process without making any changes to your actual database.

## Need Help?

If you need further assistance, please refer to:
- The complete `RELEASE_NOTES_V5.0.6.md` for details about all changes
- The `README.md` file for general PrintShop usage instructions
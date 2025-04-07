# PrintShop v5.0.6 Installation Guide

This guide will help you update your PrintShop installation to v5.0.6 with critical fixes for material tracking in quotes and n-up printing.

## Prerequisites

- PrintShop v5.0.0 or newer
- Python 3.8 or newer
- pip (Python package manager)
- PostgreSQL database

## Installation Steps

1. **Extract the ZIP package**
   ```
   unzip printshop_v5.0.6_20250405_161151.zip -d printshop_update
   cd printshop_update
   ```

2. **Update your existing installation**
   - Copy the updated files to your installation directory:
     - models.py
     - routes.py
     - pdf_generator.py

3. **Apply database migrations**
   Run the migration scripts in sequence:
   ```
   python migrations/v506_update_migration.py
   python migrations/ensure_quote_item_material.py
   python migrations/ensure_nup_print_column.py
   ```
   
   These scripts will:
   - Create the quote_item_material table if it doesn't exist
   - Add n-up column to quote items if missing
   - Migrate existing quote item descriptions to materials

4. **Restart the application**
   ```
   python main.py
   ```
   The application should now be running at http://0.0.0.0:5000 with all fixes applied.

## Verifying the Update

After updating, check that:
1. Materials show up correctly on pull sheets
2. N-up printing options work in the quote form
3. Quote to order conversion correctly transfers materials

## Troubleshooting

If you encounter database errors:

1. Ensure your database connection is properly configured in `.env`
2. Try running the migration scripts individually 
3. Check the application logs for specific error messages

For PostgreSQL errors about reserved keywords, make sure you've applied the migration scripts properly.

## Default Admin User

The default admin credentials are:
- Username: admin
- Password: password123

**IMPORTANT**: Change these credentials immediately after verifying your installation.

## Need Help?

Refer to the README.md and RELEASE_NOTES_V5.0.6.md for more detailed information.

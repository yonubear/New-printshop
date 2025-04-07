# PrintShop v5.0.6 Release Notes

## Overview
Version 5.0.6 is a maintenance release with critical fixes for material tracking in quotes and improvements to n-up printing options.

## New Features
- Enhanced material tracking for quote items
- Improved n-up printing options integration
- Better roll paper handling and square footage calculations
- **NEW: One-step database upgrade script** for easier deployment

## Bug Fixes
- Fixed issue where materials from quotes weren't showing on pull sheets
- Fixed quoting system for n-up printing jobs
- Improved PDF generation to include all materials
- Enhanced quote to order conversion process
- Fixed authentication issues with login and session handling

## Core Components Updated
- models.py: Added QuoteItemMaterial class for better material tracking
- routes.py: Fixed imports and improved quote-to-order conversion
- pdf_generator.py: Enhanced to properly display quote materials in pull sheets
- Migration scripts: Added to ensure database schema compatibility
- update_v506_single_step.py: New one-step database upgrade tool

## Upgrade Options

### Quick Upgrade (Recommended)
1. Backup your database before upgrading
2. Run the one-step upgrade script:
   ```
   python update_v506_single_step.py
   ```
3. Restart your application

For detailed instructions, see the new QUICK_UPGRADE.md file.

### Legacy Migration Method
The traditional migration scripts are still included and can be run in sequence:
1. v506_update_migration.py - Main migration script
2. ensure_quote_item_material.py - Ensures quote item materials table exists
3. ensure_nup_print_column.py - Adds n-up column to quote items if missing

See the INSTALLATION.md file for detailed instructions on this method.

## Security Updates
- Improved authentication with proper login form validation
- Enhanced session management
- Fixed CSRF token handling

## Default Users
The default admin user has the following credentials:
- Username: admin
- Password: password123

We strongly recommend changing these credentials after installation.

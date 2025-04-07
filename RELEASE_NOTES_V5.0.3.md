# PrintShop Manager v5.0.3 Release Notes

**Release Date:** April 5, 2025

## Overview
PrintShop Manager v5.0.3 introduces enhanced support for roll paper management with square footage (sqft) pricing capabilities. This update improves the flexibility of the system for print shops that work with large format printing and roll media, allowing for more accurate cost and pricing calculations.

## New Features

### Roll Paper Management
- Added dedicated roll paper identification with new `is_roll` field
- Added roll length tracking for inventory management
- Implemented automatic square footage calculations for roll media
- Added visual indicators for roll media in the paper options list

### Square Footage Pricing
- Added pricing method selector with options for 'sheet' or 'sqft' pricing
- Added price per square foot and cost per square foot fields
- Automatically calculates total price based on dimensions and pricing method
- Dynamic form handling that shows/hides relevant fields based on pricing method

## UI Improvements
- Enhanced paper options form with better field organization
- Added automatic hiding of height field when roll paper is selected
- Improved material selection interface in saved prices form
- Better visual feedback for pricing method selection

## Database Enhancements
- Added new columns to paper_option table for roll paper support:
  - `is_roll` - Boolean flag to identify roll media
  - `roll_length` - Float field to store roll length in feet
  - `width` - Float field for paper width in inches
  - `height` - Float field for paper height in inches (for sheet media)
  - `pricing_method` - Text field for 'sheet' or 'sqft' pricing method
  - `price_per_sqft` - Float field for retail price per square foot
  - `cost_per_sqft` - Float field for cost price per square foot

## Bug Fixes
- Fixed issue with duplicated roll-specific fields in paper options templates
- Corrected display problems with pricing method selector
- Fixed SQLite compatibility issues with boolean fields

## Technical Updates
- Added comprehensive database migration scripts for both SQLite and PostgreSQL
- Added database testing utility to verify configuration
- Improved error handling for database operations
- Enhanced form validation for numeric fields

## Installation Notes

### Fresh Installation
Follow the standard installation procedure in the README.md file.

### Upgrading from v5.0.0 - v5.0.2
1. Back up your existing database
2. Run the appropriate database update script:
   - For PostgreSQL: `python add_roll_paper_complete.py`
   - For all databases: `python update_to_v503.py`
3. Restart your application server

## Known Issues
- Custom pricing calculations for roll media may require additional configuration
- Import/export functionality may need updates for full compatibility with roll media data

## Coming in Future Releases
- Enhanced inventory tracking for roll media usage
- Roll media consumption analytics
- Partial roll usage tracking
- Integration with cutting systems for optimized material usage

---

For support, bug reports, or feature requests, please contact our support team or open an issue in our issue tracker.
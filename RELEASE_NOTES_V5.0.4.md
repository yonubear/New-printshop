# PrintShop v5.0.4 Release Notes

**Release Date:** April 5, 2025

## Overview
PrintShop v5.0.4 addresses critical issues with quote materials management, improving material tracking and order conversion features.

## Hotfix Improvements

### 1. Quote Item Materials Support
- Added `QuoteItemMaterial` class to properly support materials for quote items
- Fixed issues where materials from quotes weren't being displayed on pull sheets
- Added necessary database migration scripts to ensure proper data structure

### 2. Pull Sheet Enhancements
- Updated pull sheet generation to include materials from both orders and quotes
- Improved material tracking throughout the quoting and ordering process

### 3. Quote to Order Conversion
- Added full support for converting quotes to orders with material preservation
- Orders now reference back to their source quotes for improved tracking
- All materials are automatically copied from quotes to the resulting orders

### 4. User Interface Improvements
- Added routes and support for managing quote item materials
- Improved error handling for material management

## Installation Instructions

1. Make a backup of your current installation files and database.

2. Update core files:
   ```bash
   # Replace the following files with the ones from this package
   cp models.py /path/to/your/printshop/
   cp pdf_generator.py /path/to/your/printshop/
   cp routes.py /path/to/your/printshop/
   ```

3. Run the migration script to add the quote_item_material table:
   ```bash
   python add_quote_item_material_table.py
   ```

4. Restart your PrintShop application.

## Verification
After installing the hotfix:
1. Create a new quote with materials
2. Generate a pull sheet to verify materials are showing
3. Try converting a quote to an order and verify all items and materials transfer properly

## Known Issues
- None in this release

## Future Improvements
- Improved material stock management
- Enhanced material cost vs. usage reporting
- Integration with inventory management systems

## Support
For assistance with this release, please contact the PrintShop support team.
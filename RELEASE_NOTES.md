# Print Shop Management System - Release Notes

## Version 4.1 (April 2, 2025)

### New Features
- Added comprehensive Excel template generator with multiple sheets for all import types
- Enhanced data import capabilities with detailed examples for paper options, finishing options, and print pricing
- Improved template formatting with color-coded headers and detailed instructions for each import type

## Version 4.0 (April 2, 2025)

### New Features
- Added Accounts Receivable report for tracking outstanding balances and customer payments
- Integrated payment tracking fields for orders with aging analysis (current, 1-30 days, 31-60 days, etc.)
- Added customer payment reminder email functionality
- Enhanced dashboard with financial reporting cards and direct links to reports

## Version 3.0 (March 31, 2025)

### New Features
- Added comprehensive financial reporting system with profitability analysis
- Added customer-specific job reports and time period reports
- Added materials usage and cost tracking reports
- Added "Finish Size" field to quotes system for recording when jobs need to be cut down
- Improved finishing options pricing with proper minimum price logic
- Enhanced material management with consistent selection across all orders
- Added multiple items per pull sheet (3 items per page)
- Added booklet printing calculation to quote system
- Implemented auto-calculation of prices based on per-page costs

### Fixed Issues
- Fixed initialization of price calculator JavaScript
- Resolved finishing options pricing update issues
- Corrected handling of pull sheet displays and order lists
- Fixed database inconsistencies in material linking
- Improved order and quote form validation

## Installation Instructions
1. Follow the setup guide in SETUP_GUIDE.md
2. Run the migration scripts if updating from an older version:
   - `python update_finish_size.py` (for finish size field)
   - `python update_quotes_db.py` (for booklet fields)
   - `python update_proof_db.py` (for proof system)
   - `python update_payment_tracking.py` (for accounts receivable tracking)
3. If desired, generate the comprehensive Excel template for all import types:
   - `python generate_comprehensive_template.py comprehensive_import_template.xlsx`

## Notes
- The background color has been updated to grey (#e0e0e0) as requested
- Email-based customer proof approval system includes token generation, status tracking, and customer feedback
- Pull sheets now support multiple items per page and include QR codes for SKUs
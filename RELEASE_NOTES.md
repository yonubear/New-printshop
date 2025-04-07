# Print Order Manager Release Notes

## Version 5.0.0 - Enhanced Quoting System & Stability Improvements

This major release brings significant improvements to the quoting system and overall application stability:

### New Features
- Added n-up printing options to the quote system with automated pricing calculations
- Enhanced form security with comprehensive CSRF protection across all forms
- Improved error handling for form submissions with detailed error reporting
- Robust PostgreSQL schema compatibility with automatic database validation
- Added database diagnostic and repair tools for easier maintenance

### Bug Fixes
- Fixed CSRF token errors throughout the application
- Resolved internal server errors in quote creation and editing
- Added missing database columns for n-up printing functionality
- Enhanced customer selection with proper fallback options
- Improved form validation to prevent database integrity errors

### Installation Instructions
See INSTALLATION.md for detailed installation steps for new users.

### Upgrading from 4.1.x
1. Back up your database files
2. Replace all application files with the new version
3. Run `python check_postgresql_database.py --fix` to update your database schema
4. Start the application with `python main.py` or your preferred server method

## Version 4.1.3 - PostgreSQL Compatibility

This release adds robust PostgreSQL compatibility for production deployments:

### New Features
- Full PostgreSQL database support for enterprise-grade reliability
- Enhanced database migration scripts with PostgreSQL compatibility
- Improved diagnostic tools for database troubleshooting
- Updated configuration templates with detailed PostgreSQL connection examples

### Bug Fixes
- Fixed customer discount compatibility with PostgreSQL databases
- Enhanced database connection handling and error reporting
- Improved application reliability with better database configuration detection

### Installation Instructions
See INSTALLATION.md for detailed installation steps for new users.

### Upgrading from 4.1.2
1. Update your .env file with your PostgreSQL connection string (see .env.template for examples)
2. Run `python update_customer_discount.py` to ensure your database schema is updated
3. Start the application with `python main.py`

## Version 4.1.2 - Database Path Fix

This release focuses on fixing a critical database path issue and improves the installation process:

### Bug Fixes
- Fixed database path configuration to properly use the 'instance' directory
- Improved setup.py to automatically detect and fix incorrect database paths
- Enhanced error handling during database initialization

### New Features
- Added customer discount database migration for seamless updates
- Improved installation guide with detailed steps
- Enhanced setup script that verifies permissions and fixes common issues

### Installation Instructions
See INSTALLATION.md for detailed installation steps for new users.

### Upgrading from 4.1.1
1. Run `python setup.py` to apply the database fixes
2. Start the application with `python main.py`

## Version 4.1.1 - Customer Discount Feature

### New Features
- Added customer percentage discount functionality
- Enhanced Excel template generator with discount fields
- Improved database initialization with better error handling

### Bug Fixes
- Fixed recursive template rendering errors in macros.html
- Fixed database error when creating new orders by increasing field sizes
- Enhanced signature capture reliability
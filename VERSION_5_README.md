# Print Order Manager Version 5.0.0

## Overview
Version 5.0.0 represents a major milestone for the Print Order Management System with significant enhancements to the quoting system and overall application stability. This release introduces n-up printing functionality to the quote system while improving form security and database compatibility.

## Key Improvements

### New Features
- **N-Up Printing Options**: Added comprehensive n-up printing options to the quote system with automated pricing calculations
- **Enhanced Form Security**: Implemented comprehensive CSRF protection across all forms
- **Improved Error Handling**: Enhanced form submissions with detailed error reporting
- **PostgreSQL Compatibility**: Robust schema compatibility with automatic database validation
- **Diagnostic Tools**: Added database diagnostic and repair tools for easier maintenance

### Bug Fixes
- Fixed CSRF token errors throughout the application
- Resolved internal server errors in quote creation and editing
- Added missing database columns for n-up printing functionality
- Enhanced customer selection with proper fallback options
- Improved form validation to prevent database integrity errors

## Installation Instructions

### New Installation
1. Extract the package to your server
2. Create and configure a `.env` file based on the `.env.template`
3. Run `python setup.py` to initialize the application
4. Run `python check_postgresql_database.py --fix` to ensure database compatibility
5. Start the application with `python main.py` or your preferred server method

### Upgrading from Previous Versions
1. Back up your database files
2. Replace all application files with the new version
3. Run `python check_postgresql_database.py --fix` to update your database schema
4. Start the application with `python main.py` or your preferred server method

## Server Requirements
- Python 3.8 or higher
- PostgreSQL database (recommended) or SQLite
- Web server with WSGI support (Apache/mod_wsgi recommended)

## Support
For assistance with installation or configuration, please refer to the detailed installation guides in the INSTALLATION.md and APACHE_DEPLOYMENT.md files.
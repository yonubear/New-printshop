# Print Order Manager Release Notes

## Version 5.0.1 - Square Footage Pricing & Database Fixes

This maintenance release adds square footage pricing capabilities and includes database fixes to ensure smooth operation:

### New Features
- Added square footage (sqft) pricing options to paper and print cost models
- New pricing_method field allows switching between sheet-based and sqft-based pricing
- Added width and height dimensions to paper options for accurate sqft calculations
- Enhanced database verification tool with specific checks for v5.0.1 features
- Improved paper options interface with delete functionality

### Bug Fixes
- Fixed missing delete functionality for paper options
- Added comprehensive database column verification for PostgreSQL
- Enhanced error handling for database operations
- Improved route definitions with proper error handling

### Installation Instructions
See INSTALLATION.md for detailed installation steps for new users.

### Upgrading from 5.0.0
1. Back up your database files
2. Replace all application files with the new version
3. Run `python verify_v501_database.py --fix` to update your database schema
4. Start the application with `python main.py` or your preferred server method

### Upgrading from 4.1.x
1. Back up your database files
2. Replace all application files with the new version
3. Run `python check_postgresql_database.py --fix` to update your database schema
4. Run `python verify_v501_database.py --fix` to add the new v5.0.1 columns
5. Start the application with `python main.py` or your preferred server method
#!/usr/bin/env python3
"""
Create Simplified Version 5.0.1 Export Package

This script creates a streamlined export package of the Print Shop Management System
version 5.0.1, focusing only on essential application files.

Usage:
    python create_v501_simple_package.py
"""

import os
import sys
import zipfile
import shutil
import datetime
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('package_creator')

def create_v501_simple_package():
    """Create a streamlined version 5.0.1 package with essential files"""
    # Get current date in YYYYMMDD format
    today = datetime.datetime.now().strftime('%Y%m%d')
    
    # Define package name
    package_name = f"printshop_v5.0.1_simple_{today}"
    zip_filename = f"{package_name}.zip"
    
    # Define essential files to include
    essential_files = [
        # Core application files
        'main.py',
        'app.py',
        'models.py',
        'routes.py',
        'routes_addon.py',
        'routes_customer_pricing.py',
        'routes_pickup.py',
        'routes_preview.py',
        'nextcloud_client.py',
        'email_service.py',
        'pdf_generator.py',
        'wsgi.py',
        
        # Database scripts
        'check_postgresql_database.py',
        'verify_v501_database.py',
        'update_v501_database.py',
        'add_sqft_pricing_columns.py',
        'add_sqft_pricing_complete.py',
        'fix_postgresql_order_table.sql',
        'apply_postgresql_fix.py',
        'reload_sqlalchemy_metadata.py',
        
        # Documentation
        'RELEASE_NOTES_V5.0.1.md',
        'INSTALLATION.md',
        'APACHE_DEPLOYMENT.md',
        'README.md',
        
        # Templates folder (will be added separately)
        # Static folder (will be added separately)
    ]
    
    # Create zip file
    logger.info(f"Creating zip file {zip_filename}...")
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Add individual essential files
        for file in essential_files:
            if os.path.exists(file):
                zipf.write(file, file)
                logger.info(f"Added {file}")
            else:
                logger.warning(f"File not found: {file}")
        
        # Add templates directory
        if os.path.exists('templates'):
            for root, dirs, files in os.walk('templates'):
                for file in files:
                    file_path = os.path.join(root, file)
                    zipf.write(file_path, file_path)
            logger.info("Added templates directory")
        
        # Add static directory
        if os.path.exists('static'):
            for root, dirs, files in os.walk('static'):
                for file in files:
                    file_path = os.path.join(root, file)
                    zipf.write(file_path, file_path)
            logger.info("Added static directory")
        
        # Create VERSION file
        version_content = "5.0.1"
        zipf.writestr('VERSION', version_content)
        
        # Create .env.template
        env_template = """# Database configuration
# Use one of the following options:

# Option 1: PostgreSQL with DATABASE_URL
DATABASE_URL=postgresql://username:password@localhost:5432/printshop

# Option 2: PostgreSQL with individual parameters
PGHOST=localhost
PGPORT=5432
PGDATABASE=printshop
PGUSER=username
PGPASSWORD=password

# Nextcloud configuration (optional)
NEXTCLOUD_URL=https://your-nextcloud-server.com
NEXTCLOUD_USERNAME=your_username
NEXTCLOUD_PASSWORD=your_password
NEXTCLOUD_UPLOAD_PATH=/PrintShop/Orders
"""
        zipf.writestr('.env.template', env_template)
        
        # Create README
        readme_content = """# Print Shop Manager v5.0.1

## Installation

1. Extract all files to your web server directory
2. Configure your database by copying `.env.template` to `.env` and editing the values
3. Initialize the database by running `python check_postgresql_database.py --fix`
4. Add the new square footage pricing columns by running `python verify_v501_database.py --fix`
5. Start the application with `python main.py` or using your preferred server method (e.g., Gunicorn, Apache with WSGI)

## Upgrading from v5.0.0

1. Back up your database and configuration
2. Replace all files with this version
3. Run `python verify_v501_database.py --fix` to add the new columns
4. Restart your application

## Upgrading from v4.x

1. Back up your database and configuration
2. Replace all files with this version
3. Run `python check_postgresql_database.py --fix` to update your database schema
4. Run `python verify_v501_database.py --fix` to add the new columns
5. Restart your application

## New Features

- Square footage pricing options for paper and print pricing
- Enhanced database verification and repair tools
- Improved paper options management with proper delete functionality

See RELEASE_NOTES_V5.0.1.md for more details.
"""
        zipf.writestr('README_V5.0.1.md', readme_content)
    
    logger.info(f"Package created successfully: {zip_filename}")
    logger.info(f"Size: {os.path.getsize(zip_filename) / (1024*1024):.2f} MB")
    
    return zip_filename

if __name__ == "__main__":
    create_v501_simple_package()
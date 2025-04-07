#!/usr/bin/env python3
"""
Create Simple Version 5.0.0 Export Package

This script creates a streamlined export package of the Print Shop Management System
version 5.0.0, focusing only on essential application files.

Usage:
    python create_simple_v5_package.py
"""

import os
import sys
import zipfile
import datetime

def create_simple_v5_package():
    """Create a streamlined version 5.0.0 package with essential files"""
    # Get current date for timestamp
    current_date = datetime.datetime.now().strftime("%Y%m%d")
    
    # Define package name
    package_name = f"printshop_v5.0.0_{current_date}"
    package_path = f"{package_name}.zip"
    
    # Check if package already exists
    if os.path.exists(package_path):
        print(f"Package {package_path} already exists. Removing...")
        os.remove(package_path)
    
    # Define essential files to include
    essential_directories = [
        'static',
        'templates',
    ]
    
    essential_files = [
        'app.py',
        'email_service.py',
        'main.py',
        'models.py',
        'nextcloud_client.py',
        'pdf_generator.py',
        'routes.py',
        'routes_addon.py',
        'routes_customer_pricing.py',
        'routes_pickup.py',
        'routes_preview.py',
        'APACHE_DEPLOYMENT.md',
        'INSTALLATION.md',
        'README.md',
        'RELEASE_NOTES.md',
        '.env.template',
        'check_postgresql_database.py',
        'fix_database.py',
        'fix_order_pickup_columns.py',
        'init_db.py',
        'setup.py',
        'update_customer_discount.py',
        'update_db.py',
        'wsgi.py',
    ]
    
    # Create ZIP archive
    print(f"Creating ZIP archive {package_path}...")
    file_count = 0
    
    with zipfile.ZipFile(package_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Add essential files
        for file in essential_files:
            if os.path.exists(file):
                zipf.write(file)
                file_count += 1
                print(f"Added file: {file}")
        
        # Add directories
        for directory in essential_directories:
            for root, dirs, files in os.walk(directory):
                for file in files:
                    # Skip unwanted file types
                    if file.endswith(('.pyc', '.pyo', '.DS_Store')):
                        continue
                    
                    file_path = os.path.join(root, file)
                    zipf.write(file_path)
                    file_count += 1
                    
                    if file_count % 50 == 0:
                        print(f"Added {file_count} files...")
        
        # Create empty instance directory
        zipf.writestr('instance/.keep', '')
    
    print(f"Package created successfully: {package_path}")
    print(f"Total files included: {file_count}")
    return package_path

if __name__ == "__main__":
    try:
        package_path = create_simple_v5_package()
        print(f"\nVersion 5.0.0 package created successfully: {package_path}")
        print("\nKey improvements in Version 5.0.0:")
        print("- N-up printing options with automated pricing")
        print("- Enhanced form security with CSRF protection")
        print("- Improved error handling and validation")
        print("- Robust PostgreSQL schema compatibility")
        print("- Database diagnostic and repair tools")
    except Exception as e:
        print(f"Error creating package: {e}", file=sys.stderr)
        sys.exit(1)
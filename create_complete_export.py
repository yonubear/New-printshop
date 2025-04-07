#!/usr/bin/env python3
"""
Create Complete Export Package

This script creates a complete export package of the Print Shop Management System,
including all files, database, and configurations for a full backup.

Usage:
    python create_complete_export.py
"""

import os
import shutil
import zipfile
from datetime import datetime
import time

def create_complete_export():
    """Create a complete export package with all files and database"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    export_name = f"printshop_complete_v4.1.3_{timestamp}"
    
    # Create zip file
    zip_filename = f"{export_name}.zip"
    
    # Essential files and directories to include
    essential_files = [
        # Python files
        'main.py', 'app.py', 'models.py', 'routes.py', 'email_service.py',
        'pdf_generator.py', 'nextcloud_client.py', 'init_db.py',
        'export_db.py', 'import_db.py', 'export_files.py',
        'update_finish_size.py', 'update_payment_tracking.py',
        'update_quotes_db.py', 'update_proof_db.py',
        'generate_comprehensive_template.py', 'create_admin_user.py',
        
        # Database utilities and migrations
        'update_customer_discount.py', 'fix_database.py', 'diagnose_db.py',
        'test_db_connection.py', 'update_tracking_code.py', 'routes_addon.py',
        'routes_preview.py', 'routes_customer_pricing.py', 'routes_pickup.py',
        
        # Configuration and documentation
        '.env.template', 'README.md', 'SETUP_GUIDE.md', 'RELEASE_NOTES.md',
        'dependencies.txt', 'INSTALLATION.md', 'APACHE_DEPLOYMENT.md',
        
        # Directories
        'static/', 'templates/', 'instance/'
    ]
    
    def should_include(path):
        # Only include essential files
        for essential in essential_files:
            if path.startswith(essential):
                return True
                
        return False
    
    print(f"Creating complete export package: {zip_filename}")
    # Use a fixed date for zip entries (January 1, 2025)
    zip_date = (2025, 1, 1, 0, 0, 0)
    
    # Create a list of specific files to include
    specific_files = [f for f in essential_files if not f.endswith('/')]
    
    # Create a list of directories to walk through
    directories = [d.rstrip('/') for d in essential_files if d.endswith('/')]
    
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # First add individual files
        for file in specific_files:
            file_path = file
            if os.path.exists(file_path):
                print(f"Adding file: {file_path}")
                # Create a ZipInfo object with a safe date
                zi = zipfile.ZipInfo(file_path, zip_date)
                zi.external_attr = 0o644 << 16  # Permissions
                with open(file_path, 'rb') as f:
                    zipf.writestr(zi, f.read())
        
        # Then add files from specified directories
        for directory in directories:
            if not os.path.exists(directory):
                print(f"Warning: Directory {directory} not found, skipping...")
                continue
                
            for root, dirs, files in os.walk(directory):
                for file in files:
                    file_path = os.path.join(root, file)
                    # Skip hidden files and directories
                    if '/.' in file_path or file.startswith('.'):
                        continue
                        
                    print(f"Adding from directory: {file_path}")
                    # Create a ZipInfo object with a safe date
                    zi = zipfile.ZipInfo(file_path, zip_date)
                    zi.external_attr = 0o644 << 16  # Permissions
                    with open(file_path, 'rb') as f:
                        zipf.writestr(zi, f.read())
    
    file_size = os.path.getsize(zip_filename) / 1024  # KB
    print(f"\nComplete export package created: {zip_filename}")
    print(f"Size: {file_size:.1f} KB")
    return zip_filename

if __name__ == "__main__":
    zip_file = create_complete_export()
    print("\nThis export package contains:")
    print("- All application code")
    print("- Database files (in instance directory)")
    print("- Configuration templates")
    print("- Static files and templates")
    print("- Documentation and setup guides")
    print("\nTo restore this backup:")
    print("1. Extract the files to your desired location")
    print("2. Install dependencies: pip install -r dependencies.txt")
    print("3. Run the application: python main.py")
#!/usr/bin/env python3
"""
Create Version 5.0.1 Export Package

This script creates a complete export package of the Print Shop Management System
version 5.0.1, including all files, database, and configurations.

Usage:
    python create_v501_package.py
"""

import os
import sys
import zipfile
import shutil
import datetime
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('package_creator')

def create_v501_package():
    """Create a complete version 5.0.1 package with all files and database"""
    # Get current date in YYYYMMDD format
    today = datetime.datetime.now().strftime('%Y%m%d')
    
    # Define package name
    package_name = f"printshop_v5.0.1_{today}"
    
    # Define file paths
    zip_filename = f"{package_name}.zip"
    temp_dir = package_name
    
    # Create temporary directory
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    # Define files to exclude
    exclude_patterns = [
        '__pycache__', 
        '*.pyc', 
        '.git', 
        '.env',
        'instance',
        '*.zip',
        'printshop_export_*',
        'printshop_complete_*',
        'printshop_v*',
        'venv',
        'env',
        '.venv',
        'instance',
        'test_instance',
        'node_modules',
        'printshop.db',
        '.replit',
        'replit.nix'
    ]
    
    # Define function to check if a file should be included
    def should_include(path):
        path_str = str(path)
        
        # Check exclusion patterns
        for pattern in exclude_patterns:
            if pattern.startswith('*') and pattern.endswith('*'):
                if pattern[1:-1] in path_str:
                    return False
            elif pattern.startswith('*'):
                if path_str.endswith(pattern[1:]):
                    return False
            elif pattern.endswith('*'):
                if path_str.startswith(pattern[:-1]):
                    return False
            elif pattern in path_str:
                return False
        
        # Include if not excluded
        return True
    
    # Copy files to temporary directory
    logger.info(f"Creating package in {temp_dir}...")
    
    # First, get a list of all files to copy
    files_to_copy = []
    for root, dirs, files in os.walk('.'):
        # Skip excluded directories
        dirs[:] = [d for d in dirs if should_include(os.path.join(root, d))]
        
        for file in files:
            src_path = os.path.join(root, file)
            if should_include(src_path):
                files_to_copy.append(src_path)
    
    # Copy files
    for src_path in files_to_copy:
        # Skip the package file itself
        if src_path == f"./{zip_filename}":
            continue
            
        # Get normalized path
        src_path_norm = os.path.normpath(src_path)
        if src_path_norm.startswith('./'):
            src_path_norm = src_path_norm[2:]
        elif src_path_norm.startswith('.\\'):
            src_path_norm = src_path_norm[2:]
            
        # Create destination path
        dst_path = os.path.join(temp_dir, src_path_norm)
        dst_dir = os.path.dirname(dst_path)
        
        # Create directory if it doesn't exist
        os.makedirs(dst_dir, exist_ok=True)
        
        # Copy file
        try:
            shutil.copy2(src_path, dst_path)
        except Exception as e:
            logger.warning(f"Failed to copy {src_path}: {e}")
    
    # Create special version files
    with open(os.path.join(temp_dir, 'VERSION'), 'w') as f:
        f.write('5.0.1')
    
    # Copy the new verification script with execute permissions
    verify_script_src = 'verify_v501_database.py'
    verify_script_dst = os.path.join(temp_dir, verify_script_src)
    if os.path.exists(verify_script_src):
        shutil.copy2(verify_script_src, verify_script_dst)
        # Make executable
        os.chmod(verify_script_dst, 0o755)
    
    # Copy new release notes
    release_notes_src = 'RELEASE_NOTES_V5.0.1.md'
    if os.path.exists(release_notes_src):
        shutil.copy2(release_notes_src, os.path.join(temp_dir, 'RELEASE_NOTES.md'))
    
    # Create a template environment file
    with open(os.path.join(temp_dir, '.env.template'), 'w') as f:
        f.write("""# Database configuration
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
""")
    
    # Create README and update instructions
    with open(os.path.join(temp_dir, 'README_V5.0.1.md'), 'w') as f:
        f.write("""# Print Shop Manager v5.0.1

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

See RELEASE_NOTES.md for more details.
""")
    
    # Create zip file
    logger.info(f"Creating zip file {zip_filename}...")
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                file_path = os.path.join(root, file)
                zipf.write(file_path, arcname=os.path.relpath(file_path, temp_dir))
    
    # Clean up temporary directory
    shutil.rmtree(temp_dir)
    
    logger.info(f"Package created successfully: {zip_filename}")
    logger.info(f"Size: {os.path.getsize(zip_filename) / (1024*1024):.2f} MB")
    
    return zip_filename

if __name__ == "__main__":
    create_v501_package()
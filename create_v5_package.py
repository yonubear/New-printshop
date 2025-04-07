#!/usr/bin/env python3
"""
Create Version 5.0.0 Export Package

This script creates a complete export package of the Print Shop Management System
version 5.0.0, including all files, database, and configurations.

Usage:
    python create_v5_package.py
"""

import os
import sys
import shutil
import zipfile
import datetime
from pathlib import Path

def create_v5_package():
    """Create a complete version 5.0.0 package with all files and database"""
    # Get current date for timestamp
    current_date = datetime.datetime.now().strftime("%Y%m%d")
    
    # Define package name
    package_name = f"printshop_v5.0.0_{current_date}"
    package_path = f"{package_name}.zip"
    
    # Check if package already exists
    if os.path.exists(package_path):
        print(f"Package {package_path} already exists. Removing...")
        os.remove(package_path)
    
    # Create temporary directory for package contents
    if os.path.exists(package_name):
        print(f"Temporary directory {package_name} already exists. Removing...")
        shutil.rmtree(package_name)
    
    os.makedirs(package_name)
    
    # Define files to exclude from package
    exclude_patterns = [
        '.git', '__pycache__', '*.pyc', '*.pyo', '.DS_Store',
        '*.db', 'instance', 'test_instance', 'venv', 'env',
        'node_modules', '.pytest_cache', '.coverage', '.vscode',
        'htmlcov', 'printshop_export_*', 'printshop_complete_*',
        'printshop_v*.zip', 'printshop_download_*', '.env',
        '.github', 'logs', 'tmp'
    ]
    
    # Function to check if a file should be included
    def should_include(path):
        path_str = str(path)
        # Always include essential files
        essential_files = ['requirements.txt', 'main.py', 'models.py', 'routes.py', 
                         'app.py', 'INSTALLATION.md', 'RELEASE_NOTES.md',
                         '.env.template', 'setup.py', 'check_postgresql_database.py',
                         'LICENSE', 'README.md', 'APACHE_DEPLOYMENT.md']
        
        for file in essential_files:
            if path_str.endswith(file):
                return True
                
        # Check exclude patterns
        for pattern in exclude_patterns:
            if pattern.startswith('*'):
                if path_str.endswith(pattern[1:]):
                    return False
            elif pattern in path_str:
                return False
        
        # Include all other files
        return True
    
    # Copy files to temporary directory
    print(f"Creating package {package_path}...")
    file_count = 0
    
    for root, dirs, files in os.walk('.'):
        # Skip excluded directories
        dirs[:] = [d for d in dirs if should_include(os.path.join(root, d))]
        
        for file in files:
            src_path = os.path.join(root, file)
            
            if should_include(src_path):
                # Create relative path for destination
                if root.startswith('./'):
                    rel_dir = root[2:]
                elif root == '.':
                    rel_dir = ''
                else:
                    rel_dir = root
                
                # Create directory structure in package
                dst_dir = os.path.join(package_name, rel_dir)
                if not os.path.exists(dst_dir):
                    os.makedirs(dst_dir)
                
                # Copy file
                dst_path = os.path.join(package_name, rel_dir, file)
                shutil.copy2(src_path, dst_path)
                file_count += 1
                
                if file_count % 100 == 0:
                    print(f"Copied {file_count} files...")
    
    # Create empty instance directory
    instance_dir = os.path.join(package_name, 'instance')
    if not os.path.exists(instance_dir):
        os.makedirs(instance_dir)
    
    # Zip the package
    print(f"Creating ZIP archive {package_path}...")
    with zipfile.ZipFile(package_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(package_name):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, package_name)
                zipf.write(file_path, arcname)
    
    # Clean up temporary directory
    print("Cleaning up temporary files...")
    shutil.rmtree(package_name)
    
    print(f"Package created successfully: {package_path}")
    print(f"Total files included: {file_count}")
    return package_path

if __name__ == "__main__":
    try:
        package_path = create_v5_package()
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
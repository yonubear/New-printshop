#!/usr/bin/env python3
"""
Verify Export Package

This script verifies the contents of an export package to ensure all required files
are present. It also checks for integrity of key components and prints a summary.

Usage:
    python verify_export.py <export_package.zip>
"""

import os
import sys
import zipfile

def verify_export(zip_filename):
    """Verify the contents of the export package"""
    
    if not os.path.exists(zip_filename):
        print(f"Error: File {zip_filename} not found")
        return False
        
    print(f"Verifying export package: {zip_filename}")
    print("-" * 60)
    
    # Key components that must be present
    required_files = [
        'main.py', 'app.py', 'models.py', 'routes.py', 
        '.env.template', 'dependencies.txt', 'README.md', 
        'SETUP_GUIDE.md', 'RELEASE_NOTES.md'
    ]
    
    required_directories = [
        'static/', 'templates/', 'instance/'
    ]
    
    try:
        with zipfile.ZipFile(zip_filename, 'r') as zipf:
            file_list = zipf.namelist()
            
            # Verify required files
            missing_files = []
            for req_file in required_files:
                if req_file not in file_list:
                    missing_files.append(req_file)
            
            # Verify required directories
            directories_found = {d: False for d in required_directories}
            for filename in file_list:
                for directory in required_directories:
                    if filename.startswith(directory):
                        directories_found[directory] = True
            
            missing_directories = [d for d, found in directories_found.items() if not found]
            
            # Print summary
            print(f"Total files: {len(file_list)}")
            print(f"Database included: {'instance/printshop.db' in file_list}")
            
            if missing_files:
                print("\nWarning: Missing required files:")
                for file in missing_files:
                    print(f"  - {file}")
            else:
                print("\nAll required files are present.")
                
            if missing_directories:
                print("\nWarning: Missing required directories:")
                for directory in missing_directories:
                    print(f"  - {directory}")
            else:
                print("All required directories are present.")
            
            # Check file sizes
            db_size = 0
            if 'instance/printshop.db' in file_list:
                db_size = zipf.getinfo('instance/printshop.db').file_size / 1024  # KB
                print(f"\nDatabase size: {db_size:.1f} KB")
            
            # Print the size of the export package
            package_size = os.path.getsize(zip_filename) / 1024  # KB
            print(f"Package size: {package_size:.1f} KB")
            
            # Check if there are no missing components
            if not missing_files and not missing_directories:
                print("\nVerification successful! The export package contains all required components.")
                return True
            else:
                print("\nVerification failed. Some required components are missing.")
                return False
                
    except zipfile.BadZipFile:
        print(f"Error: {zip_filename} is not a valid ZIP file")
        return False
    except Exception as e:
        print(f"Error verifying export package: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        # Find the latest printshop_complete zip file
        complete_exports = [f for f in os.listdir('.') if f.startswith('printshop_complete_') and f.endswith('.zip')]
        if complete_exports:
            latest_export = sorted(complete_exports)[-1]
            print(f"No export package specified, using latest: {latest_export}")
            verify_export(latest_export)
        else:
            print("Error: No export package specified and no printshop_complete_*.zip files found")
            print("Usage: python verify_export.py <export_package.zip>")
    else:
        verify_export(sys.argv[1])
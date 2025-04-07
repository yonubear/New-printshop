#!/usr/bin/env python3
"""
Download Print Shop Management System Version 5.0.0

This script helps users download the latest Version 5.0.0 of the 
Print Shop Management System with detailed release information.

Usage:
    python download_v5.py
"""

import os
import sys
import shutil
import datetime

def copy_v5_package():
    """Copy the Version 5.0.0 package to a user-friendly name"""
    # Find the latest v5 package
    package_name = None
    latest_package = None
    
    for file in os.listdir('.'):
        if file.startswith('printshop_v5.0.0_') and file.endswith('.zip'):
            if latest_package is None or file > latest_package:
                latest_package = file
                package_name = file
    
    if not package_name:
        print("ERROR: Could not find Version 5.0.0 package.")
        sys.exit(1)
    
    # Define user-friendly name
    user_friendly_name = "PrintShopManager_v5.0.0.zip"
    
    # Copy the file with the user-friendly name
    print(f"Creating downloadable file: {user_friendly_name}")
    shutil.copy2(package_name, user_friendly_name)
    
    # Get file size
    file_size = os.path.getsize(user_friendly_name)
    file_size_mb = file_size / (1024 * 1024)
    
    print("\n" + "=" * 70)
    print("PRINT SHOP MANAGEMENT SYSTEM - VERSION 5.0.0")
    print("=" * 70)
    print(f"\nPackage ready for download: {user_friendly_name}")
    print(f"Size: {file_size_mb:.2f} MB")
    print("\nKey improvements in Version 5.0.0:")
    print("- N-up printing options with automated pricing")
    print("- Enhanced form security with CSRF protection")
    print("- Improved error handling and validation")
    print("- Robust PostgreSQL schema compatibility")
    print("- Database diagnostic and repair tools")
    print("\nFor detailed installation instructions, please refer to:")
    print("- VERSION_5_README.md - Quick overview and upgrade guide")
    print("- INSTALLATION.md - Complete installation guide")
    print("- APACHE_DEPLOYMENT.md - Apache server configuration")
    print("\nAfter downloading, extract all files to your server directory.")
    print("=" * 70)
    
    return user_friendly_name

if __name__ == "__main__":
    try:
        file_name = copy_v5_package()
        print(f"\nDownload the file: {file_name}")
    except Exception as e:
        print(f"Error preparing download: {e}", file=sys.stderr)
        sys.exit(1)
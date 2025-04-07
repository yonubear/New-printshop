#!/usr/bin/env python3
"""
Download Latest Print Shop Management System Package (v4.1.1)

This script helps users get the latest version of the Print Shop Management System.
It creates a copy of the latest available package and provides instructions
for downloading and installation.

New in v4.1.1:
- Added missing qrcode dependency for pull sheet QR code generation
- Fixed database initialization issues
- Improved error handling and setup instructions
- Enhanced robustness for first-time users

New in v4.1:
- Comprehensive Excel template generator with multiple sheets for all import types
- Enhanced data import capabilities with detailed examples
- Improved template formatting with color-coded headers and instructions
"""

import os
import sys
import glob
import shutil
import re
from datetime import datetime

CURRENT_VERSION = "4.1.1"

def extract_version_from_filename(filename):
    """Try to extract version number from filename like printshop_export_final_v4.1.1.zip"""
    match = re.search(r'v(\d+\.\d+\.\d+)', filename)
    if match:
        return match.group(1)
    
    # Fallback to simpler version format (major.minor)
    match = re.search(r'v(\d+\.\d+)', filename)
    if match:
        return match.group(1)
    
    return None

def main():
    # Find the latest export package
    export_files = glob.glob("printshop_export_final_v*.zip")
    
    if not export_files:
        export_files = glob.glob("printshop_export_final_*.zip")
    
    if not export_files:
        export_files = glob.glob("printshop_export_*.zip")
    
    if not export_files:
        print("Error: No export packages found.")
        sys.exit(1)
    
    # Sort by modification time (most recent first)
    latest_file = sorted(export_files, key=lambda x: os.path.getmtime(x), reverse=True)[0]
    
    # Try to extract version from filename
    version = extract_version_from_filename(latest_file) or CURRENT_VERSION
    
    # Create a new filename with today's date and version
    today = datetime.now().strftime("%Y%m%d")
    download_file = f"printshop_v{version}_download_{today}.zip"
    
    # Create a copy with the new name
    shutil.copy2(latest_file, download_file)
    
    file_size = os.path.getsize(download_file) / 1024  # KB
    
    print("\n" + "=" * 70)
    print(f"Print Shop Management System v{version}")
    print("=" * 70)
    print(f"Download Package Created: {download_file}")
    print(f"File Size: {file_size:.1f} KB")
    print("\nWhat's New in Version 4.1.1:")
    print("- Added missing qrcode dependency for pull sheet QR code generation")
    print("- Fixed database initialization issues for first-time users")
    print("- Improved error handling and setup instructions")
    print("- Enhanced robustness of the application")
    print("=" * 70)
    print("\nTo download this file, use one of these methods:")
    print("\n1. From the file browser panel:")
    print("   - Right-click on the file")
    print("   - Select 'Download'")
    print("\n2. Using terminal/command line:")
    print(f"   curl -o printshop_v{version}.zip https://your-replit-domain/{download_file}")
    print("\nAfter downloading, follow installation instructions in SETUP_GUIDE.md")
    print("=" * 70 + "\n")

if __name__ == "__main__":
    main()
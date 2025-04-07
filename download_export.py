#!/usr/bin/env python3
"""
Download Export Package

This script helps the user select which export package they want to download
and provides information about each package.

Usage:
    python download_export.py
"""

import os
import sys
import shutil
from datetime import datetime

def get_file_size(filename):
    """Get file size in human-readable format"""
    size_bytes = os.path.getsize(filename)
    
    if size_bytes < 1024:
        return f"{size_bytes} bytes"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"

def list_export_packages():
    """List all available export packages"""
    # Find all export packages
    export_files = [
        f for f in os.listdir('.')
        if (f.startswith('printshop_v') or f.startswith('printshop_complete_') or f.startswith('printshop_export_final_'))
        and f.endswith('.zip')
    ]
    
    if not export_files:
        print("No export packages found.")
        return None
    
    # Group files by type
    standard_exports = [f for f in export_files if f.startswith('printshop_v')]
    complete_exports = [f for f in export_files if f.startswith('printshop_complete_')]
    minimal_exports = [f for f in export_files if f.startswith('printshop_export_final_')]
    
    # Sort each group by name (which should sort by version and date)
    standard_exports.sort(reverse=True)
    complete_exports.sort(reverse=True)
    minimal_exports.sort(reverse=True)
    
    # Create a list of all packages with their types
    all_packages = []
    
    # Add standard exports
    for i, file in enumerate(standard_exports):
        all_packages.append(("standard", i, file))
    
    # Add complete exports
    for i, file in enumerate(complete_exports):
        all_packages.append(("complete", i, file))
    
    # Add minimal exports
    for i, file in enumerate(minimal_exports):
        all_packages.append(("minimal", i, file))
    
    # Print the packages
    print("\nAvailable Export Packages:")
    print("-" * 80)
    print(f"{'#':<3} {'Type':<10} {'Size':<10} {'Filename'}")
    print("-" * 80)
    
    for i, (type_name, _, filename) in enumerate(all_packages):
        file_size = get_file_size(filename)
        print(f"{i+1:<3} {type_name:<10} {file_size:<10} {filename}")
    
    return all_packages

def copy_export_package(package_info):
    """Copy the selected export package to a user-friendly name"""
    package_type, _, filename = package_info
    
    # Create a user-friendly destination name
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if "v4.1.1" in filename:
        version = "v4.1.1"
    elif "v4.1" in filename:
        version = "v4.1"
    elif "v4" in filename:
        version = "v4.0"
    else:
        version = "latest"
    
    if package_type == "standard":
        dest_name = f"printshop_{version}_standard_{timestamp}.zip"
        description = "Standard export package (recommended for most users)"
    elif package_type == "complete":
        dest_name = f"printshop_{version}_complete_{timestamp}.zip"
        description = "Complete export package with database included"
    else:
        dest_name = f"printshop_{version}_minimal_{timestamp}.zip"
        description = "Minimal export package (code only)"
    
    # Copy the file
    shutil.copy2(filename, dest_name)
    
    print("\n" + "=" * 80)
    print(f"Export Package: {description}")
    print("=" * 80)
    print(f"Source: {filename}")
    print(f"Copied to: {dest_name}")
    print(f"Size: {get_file_size(dest_name)}")
    print(f"Version: {version}")
    print("=" * 80)
    print("\nTo download this file:")
    print("1. From the file browser panel:")
    print(f"   - Find '{dest_name}'")
    print("   - Right-click and select 'Download'")
    print("\n2. Using terminal/command line:")
    print(f"   curl -o printshop_{version}.zip https://your-replit-domain/{dest_name}")
    print("\nAfter downloading, follow installation instructions in SETUP_GUIDE.md")
    print("=" * 80)
    
    return dest_name

def main():
    """Main function"""
    print("Print Shop Management System - Export Package Downloader")
    print("=" * 80)
    print("This utility helps you select and download an export package.")
    print("Different package types are available based on your needs:")
    print("  - Standard: Recommended for most users")
    print("  - Complete: Includes database with sample data")
    print("  - Minimal: Code only, for clean installations or developers")
    
    # List all available packages
    all_packages = list_export_packages()
    
    if not all_packages:
        return
    
    # Ask the user to select a package
    while True:
        try:
            selection = input("\nEnter the number of the package you want to download (or 'q' to quit): ")
            
            if selection.lower() == 'q':
                print("Exiting...")
                return
            
            selection = int(selection)
            if 1 <= selection <= len(all_packages):
                # Copy the selected package
                selected_package = all_packages[selection-1]
                dest_name = copy_export_package(selected_package)
                break
            else:
                print(f"Invalid selection. Please enter a number between 1 and {len(all_packages)}.")
        except ValueError:
            print("Invalid input. Please enter a number or 'q' to quit.")
    
    print("\nThank you for using the Print Shop Management System!")

if __name__ == "__main__":
    main()
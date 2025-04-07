#!/usr/bin/env python3
"""
Create a hotfix package for V5.0.4 with Quote Item Material fixes and other improvements

This script creates a ZIP package with updated files for the PrintShop v5.0.4 hotfix.
The package includes:
- Updated models.py with QuoteItemMaterial class
- Updated pdf_generator.py to include quote materials in pull sheets
- Migration script for the new quote_item_material table
- Updated routes.py with quote item material management routes
- Hotfix installation guide

Usage:
    python create_v504_hotfix_package.py
"""

import os
import zipfile
import shutil
import datetime
import tempfile
from pathlib import Path

# Configuration
VERSION = "5.0.4"
TIMESTAMP = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
PACKAGE_NAME = f"printshop_v{VERSION}_hotfix_{TIMESTAMP}"

# Files to include in the package
FILES_TO_INCLUDE = [
    # Core files with fixes
    'models.py',                           # Added QuoteItemMaterial class
    'pdf_generator.py',                    # Updated pull sheet generation
    'routes.py',                           # Added quote material routes
    
    # Migration scripts
    'add_quote_item_material_table.py',    # Create quote_item_material table
    
    # Installation/documentation
    'README.md',
    'RELEASE_NOTES_V5.0.4.md',
]

def create_hotfix_readme():
    """Create a README file for the hotfix package"""
    readme_content = f"""# PrintShop v{VERSION} Hotfix - {datetime.datetime.now().strftime("%Y-%m-%d")}

## Overview
This hotfix package addresses issues with quote materials not showing up in pull sheets and fixes various related bugs.

## Included Fixes
- Added QuoteItemMaterial class to models.py
- Updated pdf_generator.py to include quote materials in pull sheets
- Added routes for managing quote item materials
- Migration script for adding the quote_item_material table
- Improved conversion from quotes to orders

## Installation Instructions

1. Make a backup of your current installation files and database.

2. Update core files:
   ```bash
   # Replace the following files with the ones from this package
   cp models.py /path/to/your/printshop/
   cp pdf_generator.py /path/to/your/printshop/
   cp routes.py /path/to/your/printshop/
   ```

3. Run the migration script to add the quote_item_material table:
   ```bash
   python add_quote_item_material_table.py
   ```

4. Restart your PrintShop application.

## Verification
After installing the hotfix:
1. Create a new quote with materials
2. Generate a pull sheet to verify materials are showing
3. Try converting a quote to an order and verify all items and materials transfer properly

"""
    
    with open('HOTFIX_README.md', 'w') as f:
        f.write(readme_content)
    
    return 'HOTFIX_README.md'

def create_package():
    """Create the hotfix package zip file"""
    # Create temp dir for package contents
    temp_dir = tempfile.mkdtemp()
    package_dir = os.path.join(temp_dir, PACKAGE_NAME)
    os.makedirs(package_dir, exist_ok=True)
    
    # Create hotfix README
    hotfix_readme = create_hotfix_readme()
    FILES_TO_INCLUDE.append(hotfix_readme)
    
    # Copy files to package directory
    for filename in FILES_TO_INCLUDE:
        if os.path.exists(filename):
            shutil.copy2(filename, package_dir)
            print(f"Added {filename} to package")
        else:
            print(f"Warning: {filename} not found, skipping")
    
    # Create the zip file
    zip_filename = f"{PACKAGE_NAME}.zip"
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(package_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, package_dir)
                zipf.write(file_path, arcname)
    
    # Clean up
    shutil.rmtree(temp_dir)
    os.remove(hotfix_readme)  # Remove the temporary README file
    
    print(f"\nPackage created: {zip_filename}")
    return zip_filename

if __name__ == "__main__":
    print(f"Creating PrintShop v{VERSION} hotfix package...")
    package_file = create_package()
    print(f"Hotfix package created successfully: {package_file}")
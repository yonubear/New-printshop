#!/usr/bin/env python3
"""
Update Export Package

This script creates an updated export package that includes all required dependencies
including the qrcode package that was missing from the original export.

Usage:
    python update_export.py
"""

import os
import shutil
import zipfile
from datetime import datetime
import subprocess

def create_updated_export():
    """Create an updated export package with all dependencies"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    export_dir = f"printshop_export_updated_{timestamp}"
    
    # Create export directory
    os.makedirs(export_dir, exist_ok=True)
    
    # Copy all Python files
    for file in os.listdir('.'):
        if file.endswith('.py') or file == 'dependencies.txt' or file == '.env.template':
            shutil.copy2(file, os.path.join(export_dir, file))
    
    # Copy static and templates directories
    for directory in ['static', 'templates']:
        if os.path.exists(directory):
            shutil.copytree(directory, os.path.join(export_dir, directory), dirs_exist_ok=True)
    
    # Copy documentation
    for doc in ['README.md', 'SETUP_GUIDE.md', 'RELEASE_NOTES.md', 'DEPLOYMENT.md']:
        if os.path.exists(doc):
            shutil.copy2(doc, os.path.join(export_dir, doc))
    
    # Create zip file
    zip_filename = f"printshop_export_final_v4.1.1_updated.zip"
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(export_dir):
            for file in files:
                file_path = os.path.join(root, file)
                archive_path = os.path.relpath(file_path, export_dir)
                zipf.write(file_path, archive_path)
    
    # Clean up temporary directory
    shutil.rmtree(export_dir)
    
    # Update release notes
    if os.path.exists('RELEASE_NOTES.md'):
        with open('RELEASE_NOTES.md', 'r') as f:
            content = f.read()
        
        if "## Version 4.1.1" not in content:
            with open('RELEASE_NOTES.md', 'w') as f:
                updated_content = content.replace("# Release Notes", 
                                                "# Release Notes\n\n## Version 4.1.1\n\n- Added missing qrcode dependency\n- Fixed database initialization issues\n- Improved error handling and user feedback\n")
                f.write(updated_content)
    
    print(f"Updated export package created: {zip_filename}")
    print(f"Size: {os.path.getsize(zip_filename) / 1024:.1f} KB")
    return zip_filename

if __name__ == "__main__":
    zip_file = create_updated_export()
    print("\nTo run the updated export, follow these steps:")
    print("1. Download the updated export package")
    print("2. Extract the files to your desired location")
    print("3. Install dependencies: pip install -r dependencies.txt")
    print("4. Initialize the database: python init_db.py")
    print("5. Start the application: python main.py")
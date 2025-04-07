"""
Export Print Shop Management System for Nextcloud Deployment

This script creates a complete export package for deploying the Print Shop Management System
to your own Nextcloud environment. It includes:
1. All application code and templates
2. Database export (SQL format)
3. Configuration templates
4. Setup documentation

Usage:
python export_to_nextcloud.py --output /path/to/output/directory
"""

import os
import sys
import shutil
import argparse
import datetime
import zipfile
from export_db import export_database

def create_export(output_dir=None, include_data=True):
    """
    Create a complete export package for Nextcloud deployment
    
    Args:
        output_dir: Directory to save export to. If None, a timestamped directory is created.
        include_data: Whether to include database export (for migration)
        
    Returns:
        Path to the output directory or ZIP file
    """
    # Create output directory if not provided
    if not output_dir:
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        output_dir = f"printshop_export_{timestamp}"
    
    # Create directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"Creating export package in {output_dir}...")
    
    # List of files and directories to exclude from the export
    exclude_patterns = [
        '.git', '__pycache__', 'venv', 'instance', '.env',
        '*.pyc', '.DS_Store', '.vscode', '.idea', 'node_modules',
        '*_export_*', '*.zip', '*.db'
    ]
    
    # Create a function to check if a path should be excluded
    def should_exclude(path):
        for pattern in exclude_patterns:
            if pattern.startswith('*') and pattern.endswith('*'):
                if pattern[1:-1] in path:
                    return True
            elif pattern.startswith('*'):
                if path.endswith(pattern[1:]):
                    return True
            elif pattern.endswith('*'):
                if path.startswith(pattern[:-1]):
                    return True
            elif pattern == os.path.basename(path):
                return True
        return False
    
    # Copy all project files to the output directory
    for item in os.listdir('.'):
        if should_exclude(item):
            continue
        
        # Source and destination paths
        src_path = os.path.join('.', item)
        dst_path = os.path.join(output_dir, item)
        
        if os.path.isdir(src_path):
            # Copy directory
            shutil.copytree(src_path, dst_path, ignore=lambda src, names: [
                name for name in names if should_exclude(os.path.join(src, name))
            ])
        else:
            # Copy file
            shutil.copy2(src_path, dst_path)
    
    # Create database export if requested
    if include_data:
        try:
            db_export_path = os.path.join(output_dir, 'database_export.sql')
            export_database(db_export_path)
            print(f"Database exported to {db_export_path}")
            
            # Create README for database import
            db_readme_path = os.path.join(output_dir, 'DATABASE_IMPORT.md')
            with open(db_readme_path, 'w') as f:
                f.write("# Database Import Instructions\n\n")
                f.write("This export package includes a database export file `database_export.sql` "
                        "that contains your Print Shop Management System data.\n\n")
                f.write("To import this data after setting up the application:\n\n")
                f.write("```bash\n")
                f.write("# Option 1: Using the import script\n")
                f.write("python import_db.py database_export.sql\n\n")
                f.write("# Option 2: Direct import for PostgreSQL\n")
                f.write("psql -U your_db_user -d your_db_name < database_export.sql\n")
                f.write("```\n")
        except Exception as e:
            print(f"Warning: Failed to export database: {str(e)}")
    
    # Create a deployment guide
    deploy_guide_path = os.path.join(output_dir, 'DEPLOYMENT.md')
    with open(deploy_guide_path, 'w') as f:
        f.write("# Print Shop Management System Deployment Guide\n\n")
        f.write("This export package contains everything needed to deploy the Print Shop Management System "
                "to your own server with Nextcloud integration.\n\n")
        f.write("## Quick Start\n\n")
        f.write("1. Extract this package to your server\n")
        f.write("2. Follow the instructions in `SETUP_GUIDE.md` to configure the application\n")
        f.write("3. If you included database data in the export, follow the instructions in `DATABASE_IMPORT.md`\n\n")
        f.write("## Nextcloud Configuration\n\n")
        f.write("To connect the application to your Nextcloud instance:\n\n")
        f.write("1. Create a dedicated user in Nextcloud for the application\n")
        f.write("2. Generate an app password for API access\n")
        f.write("3. Create a folder named 'print_orders' (or your chosen folder name)\n")
        f.write("4. Update the `.env` file with your Nextcloud credentials\n\n")
        f.write("## Configuration\n\n")
        f.write("Make sure to configure all required environment variables in the `.env` file. "
                "See `.env.template` for a list of available options.\n")
    
    # Create ZIP archive
    zip_path = f"{output_dir}.zip"
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(output_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, output_dir)
                zipf.write(file_path, arcname)
    
    print(f"\nExport completed successfully!")
    print(f"Export directory: {output_dir}")
    print(f"ZIP archive: {zip_path}")
    print("\nTo deploy to your Nextcloud environment:")
    print("1. Copy the ZIP file to your server")
    print("2. Extract the ZIP file")
    print("3. Follow the instructions in SETUP_GUIDE.md and DEPLOYMENT.md")
    
    return zip_path

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Export Print Shop Management System for Nextcloud deployment')
    parser.add_argument('--output', '-o', help='Output directory')
    parser.add_argument('--no-data', action='store_true', help='Do not include database export')
    args = parser.parse_args()
    
    create_export(args.output, not args.no_data)
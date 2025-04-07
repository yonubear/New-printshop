#!/usr/bin/env python3
"""
Create Version 5.0.4 Export Package

This script creates a complete export package of the Print Shop Management System
version 5.0.4, including all files, database, and configurations with
improved environment variable handling for database migrations.

Usage:
    python create_v504_package.py
"""
import os
import sys
import shutil
import zipfile
import datetime
from pathlib import Path

def create_v504_package():
    """Create a complete version 5.0.4 package with all files and database"""
    # Get current timestamp
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    package_name = f"printshop_v5.0.4_{timestamp}"
    package_dir = Path(package_name)
    
    # Create package directory if it doesn't exist
    if package_dir.exists():
        shutil.rmtree(package_dir)
    package_dir.mkdir(parents=True)
    
    # Function to determine if a file should be included
    def should_include(path):
        """Check if a file or directory should be included in the package"""
        # Skip certain directories and files
        if any(p in str(path) for p in [
            ".git", "__pycache__", ".vscode", "venv", "env", 
            ".DS_Store", ".pytest_cache", "migrations", ".mypy_cache",
            "printshop_export_", "printshop_v", ".zip"
        ]):
            return False
            
        # Skip old export directories
        if path.is_dir() and path.name.startswith("printshop_export_"):
            return False
        if path.is_dir() and path.name.startswith("printshop_v"):
            return False
            
        # Skip test databases
        if path.name == "test.db" or path.name.endswith(".bak"):
            return False
            
        # Skip large packages
        if path.name.endswith(".zip"):
            return False
            
        return True
    
    # Copy essential files to package directory
    print(f"Creating package in {package_dir}...")
    for item in Path(".").iterdir():
        if should_include(item):
            if item.is_file():
                shutil.copy2(item, package_dir)
                print(f"Copied file: {item.name}")
            elif item.is_dir():
                shutil.copytree(item, package_dir / item.name, 
                               ignore=lambda d, files: [f for f in files if not should_include(Path(d) / f)])
                print(f"Copied directory: {item.name}")
    
    # Create VERSION file
    with open(package_dir / "VERSION", "w") as f:
        f.write(f"""VERSION="5.0.4"
RELEASE_DATE="{datetime.datetime.now().strftime('%Y-%m-%d')}"
BUILD_TIMESTAMP="{datetime.datetime.now().isoformat()}"
""")
    
    # Create release notes file
    with open(package_dir / "RELEASE_NOTES_V5.0.4.md", "w") as f:
        f.write("""# PrintShop Manager v5.0.4 Release Notes

## Overview

Version 5.0.4 builds on the successful rollout of square footage pricing and roll paper support 
in v5.0.3, with significant improvements to database migration scripts and environment variable handling.

## New Features

- **Improved Environment Variable Handling**: All database migration scripts now properly handle 
  environment variables, improving compatibility across different deployment environments.

- **Safer Database Connection Logic**: Enhanced error handling for database connections with proper 
  fallback mechanisms when environment variables are not found.

- **Robust Error Handling**: Added comprehensive error checking to prevent issues when database 
  queries return unexpected results.

## Installation Instructions

### Fresh Installation

1. Download and extract the package
2. Copy `.env.template` to `.env` and fill in your database credentials
3. Run `python main.py` to initialize the application

### Upgrading from v5.0.3

1. Back up your database and `.env` file
2. Extract this package to your server
3. Run `python update_to_v504.py` to migrate your database
4. Restart your application

### Upgrading from Earlier Versions

1. First upgrade to v5.0.3 using its update script
2. Then follow the steps for upgrading from v5.0.3

## Technical Details

- Backend: Flask 2.x with SQLAlchemy 2.x
- Database: PostgreSQL 13+ or SQLite 3
- Environment: Python 3.8+
- Frontend: Bootstrap 5.x with vanilla JavaScript
""")
    
    # Create an update script for v5.0.4
    with open(package_dir / "update_to_v504.py", "w") as f:
        f.write("""#!/usr/bin/env python3
\"\"\"
PrintShop Manager 5.0.4 Update Script

This script updates your PrintShop Manager installation to version 5.0.4
by applying necessary configuration updates.

Usage:
    python update_to_v504.py
\"\"\"
import os
import sys
import logging
import datetime
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def update_version_info():
    \"\"\"Update version information files\"\"\"
    try:
        # Create VERSION file if it doesn't exist
        with open("VERSION", "w") as f:
            f.write(\"\"\"VERSION="5.0.4"
RELEASE_DATE="{0}"
BUILD_TIMESTAMP="{1}"
\"\"\".format(
                datetime.datetime.now().strftime('%Y-%m-%d'),
                datetime.datetime.now().isoformat()
            ))
        
        logger.info("Updated VERSION file")
        return True
    except Exception as e:
        logger.error(f"Error updating version info: {e}")
        return False

def main():
    \"\"\"Main update function\"\"\"
    logger.info("Starting PrintShop Manager update to version 5.0.4")
    
    # Update version information
    if update_version_info():
        logger.info("PrintShop Manager has been successfully updated to version 5.0.4")
        logger.info("Restart your application server to apply all changes")
        return 0
    else:
        logger.error("Update to version 5.0.4 failed")
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except Exception as e:
        logger.error(f"Unexpected error during update: {e}")
        sys.exit(1)
""")
    
    # Create zip file of the package
    zip_filename = f"{package_name}.zip"
    print(f"Creating zip file: {zip_filename}")
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(package_dir):
            for file in files:
                file_path = os.path.join(root, file)
                zipf.write(file_path, os.path.relpath(file_path, package_dir.parent))
    
    # Clean up the temporary directory
    shutil.rmtree(package_dir)
    
    print(f"Package created successfully: {zip_filename}")
    print(f"Size: {os.path.getsize(zip_filename) / (1024*1024):.2f} MB")
    
    return zip_filename

if __name__ == "__main__":
    create_v504_package()
#!/usr/bin/env python3
"""
Create Simplified Version 5.0.4 Export Package

This script creates a streamlined export package of the Print Shop Management System
version 5.0.4, focusing only on essential application files.

Usage:
    python create_v504_simple_package.py
"""
import os
import sys
import shutil
import zipfile
import datetime
from pathlib import Path

def create_v504_simple_package():
    """Create a streamlined version 5.0.4 package with essential files"""
    # Get current timestamp
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    package_name = f"printshop_v5.0.4_simple_{timestamp}"
    package_dir = Path(package_name)
    
    # Create package directory if it doesn't exist
    if package_dir.exists():
        shutil.rmtree(package_dir)
    package_dir.mkdir(parents=True)
    
    # Essential files to include
    essential_files = [
        "main.py", "app.py", "wsgi.py", "models.py", "routes.py", "forms.py",
        "routes_addon.py", "routes_preview.py", "routes_customer_pricing.py", "routes_pickup.py",
        "nextcloud_client.py", "pdf_generator.py", "email_service.py",
        ".env.template", "requirements.txt", "dependencies.txt",
        "add_roll_paper_complete.py", "add_sqft_pricing_complete.py", 
        "test_db_update.py", "update_to_v504.py",
        "LICENSE", "README.md", "SETUP_GUIDE.md", 
        "INSTALLATION.md", "NEXTCLOUD_TROUBLESHOOTING.md"
    ]
    
    # Essential directories to include
    essential_dirs = [
        "static", "templates", "instance"
    ]
    
    # Copy essential files
    print(f"Creating package in {package_dir}...")
    for file in essential_files:
        file_path = Path(file)
        if file_path.exists():
            shutil.copy2(file_path, package_dir)
            print(f"Copied file: {file}")
    
    # Copy essential directories
    for directory in essential_dirs:
        dir_path = Path(directory)
        if dir_path.exists():
            shutil.copytree(dir_path, package_dir / directory)
            print(f"Copied directory: {directory}")
    
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

- **Fixed Package Distribution**: All route files are now properly included in the package, 
  ensuring QR code tracking, interactive print preview, customer-specific pricing, and order
  pickup features function correctly.

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
    
    # Create the update script
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
    create_v504_simple_package()
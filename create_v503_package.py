#!/usr/bin/env python3
"""
Create Version 5.0.3 Export Package

This script creates a complete export package of the Print Shop Management System
version 5.0.3, including all files, database, and configurations.

Usage:
    python create_v503_package.py
"""
import os
import shutil
import zipfile
import datetime
import subprocess
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_v503_package():
    """Create a complete version 5.0.3 package with all files and database"""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    package_name = f"printshop_v5.0.3_{timestamp}"
    package_path = Path(package_name)
    
    # Create temporary directory for package
    if package_path.exists():
        shutil.rmtree(package_path)
    package_path.mkdir()
    
    logger.info(f"Creating package directory: {package_path}")
    
    # Define files to exclude from package
    exclude_patterns = [
        "__pycache__", 
        ".git",
        ".venv",
        "venv",
        "instance/printshop.db",
        "*.zip",
        "*.pyc",
        ".DS_Store",
        "node_modules",
        ".env",
        "printshop_export_*",
        "printshop_v*",
        f"{package_name}"
    ]
    
    # Define essential files to include regardless of exclude patterns
    essential_files = [
        "main.py",
        "app.py",
        "models.py",
        "routes.py",
        "nextcloud_client.py",
        "pdf_generator.py",
        "add_roll_paper_complete.py",
        "update_to_v503.py",
        "RELEASE_NOTES_V5.0.3.md",
        "check_postgresql_database.py",
        "init_db.py",
        "INSTALLATION.md",
        "README.md",
        "requirements.txt",
        "dependencies.txt"
    ]
    
    essential_dirs = [
        "static",
        "templates",
        "migrations"
    ]
    
    def should_include(path):
        """Check if a file or directory should be included in the package"""
        path_str = str(path)
        name = path.name
        
        # Always include essential files and directories
        if name in essential_files or name in essential_dirs:
            return True
        
        # Skip excluded patterns
        for pattern in exclude_patterns:
            if "*" in pattern:
                # Simple wildcard matching
                prefix = pattern.split("*")[0]
                if path_str.endswith(prefix) or f"/{prefix}" in path_str:
                    return False
            elif pattern in path_str or f"/{pattern}" in path_str:
                return False
        
        return True
    
    # Copy all relevant files
    files_copied = []
    dirs_copied = []
    
    # First copy essential files and directories
    for item_name in essential_files:
        item = Path(item_name)
        if item.exists() and item.is_file():
            shutil.copy2(item, package_path / item.name)
            files_copied.append(item.name)
            logger.info(f"Copied essential file: {item.name}")
    
    for item_name in essential_dirs:
        item = Path(item_name)
        if item.exists() and item.is_dir():
            shutil.copytree(item, package_path / item.name,
                          dirs_exist_ok=True,
                          ignore=shutil.ignore_patterns(*exclude_patterns))
            dirs_copied.append(item.name)
            logger.info(f"Copied essential directory: {item.name}")
    
    # Then copy remaining relevant files
    for item in Path(".").iterdir():
        if item.name not in files_copied and item.name not in dirs_copied and should_include(item):
            if item.is_dir():
                shutil.copytree(item, package_path / item.name, 
                              dirs_exist_ok=True,
                              ignore=shutil.ignore_patterns(*exclude_patterns))
                logger.info(f"Copied directory: {item.name}")
            else:
                shutil.copy2(item, package_path / item.name)
                logger.info(f"Copied file: {item.name}")
    
    # Create a .env.template file for the package
    env_template = """# PrintShop Manager Environment Configuration
# Rename this file to .env and fill in your values

# Flask Configuration
FLASK_APP=main.py
FLASK_ENV=production
FLASK_SECRET_KEY=your-secret-key-here

# PostgreSQL Database
DATABASE_URL=postgresql://user:password@localhost:5432/printshop
PGUSER=user
PGPASSWORD=password
PGHOST=localhost
PGPORT=5432
PGDATABASE=printshop

# Nextcloud Integration (Optional)
NEXTCLOUD_URL=https://your-nextcloud-server.com
NEXTCLOUD_USERNAME=your-username
NEXTCLOUD_PASSWORD=your-password
NEXTCLOUD_FOLDER=/PrintShopFiles

# Email Configuration (Optional)
MAIL_SERVER=smtp.example.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@example.com
MAIL_PASSWORD=your-email-password
MAIL_DEFAULT_SENDER=your-email@example.com

# For Twilio SMS Integration (Optional)
TWILIO_ACCOUNT_SID=your-account-sid
TWILIO_AUTH_TOKEN=your-auth-token
TWILIO_PHONE_NUMBER=your-twilio-number
"""
    
    with open(package_path / ".env.template", "w") as f:
        f.write(env_template)
    logger.info("Created .env.template file")
    
    # Create README file with version info
    readme_content = """# PrintShop Manager v5.0.3

A comprehensive print shop management system for tracking orders, managing materials,
generating quotes, and streamlining print shop operations.

## New in Version 5.0.3
- Enhanced roll paper management with square footage pricing
- Improved UI with better form field handling
- New database scripts for PostgreSQL users
- See RELEASE_NOTES_V5.0.3.md for full details

## Installation
1. Extract the package contents
2. Copy .env.template to .env and configure your environment variables
3. Install required dependencies: `pip install -r requirements.txt`
4. Initialize the database: `python init_db.py`
5. Run the application: `python main.py`

For PostgreSQL users, run the database setup script:
```bash
python add_roll_paper_complete.py
```

## Upgrading from Previous Versions
If upgrading from a previous version, make sure to:
1. Back up your database
2. Run any applicable database migration scripts
3. Update your .env file with any new environment variables

## System Requirements
- Python 3.9 or higher
- PostgreSQL 12+ or SQLite 3
- Modern web browser

See INSTALLATION.md for detailed setup instructions.
"""
    
    with open(package_path / "README.md", "w") as f:
        f.write(readme_content)
    logger.info("Created README.md file with version info")
    
    # Copy the database upgrade scripts
    upgrade_scripts = [
        "add_roll_paper_complete.py",
        "check_postgresql_database.py",
    ]
    
    logger.info("Verifying database scripts...")
    for script in upgrade_scripts:
        if Path(script).exists():
            logger.info(f"Script {script} already exists and will be included")
        else:
            logger.error(f"Script {script} not found!")
    
    # Generate version file
    version_info = """VERSION="5.0.3"
RELEASE_DATE="2025-04-05"
BUILD_TIMESTAMP="{}"
""".format(datetime.datetime.now().isoformat())
    
    with open(package_path / "VERSION", "w") as f:
        f.write(version_info)
    logger.info("Created VERSION file")
    
    # Create requirements.txt with all Python dependencies
    try:
        with open("dependencies.txt", "r") as src, open(package_path / "requirements.txt", "w") as dest:
            deps = src.read()
            dest.write(deps)
        logger.info("Created requirements.txt from dependencies.txt")
    except FileNotFoundError:
        # Generate requirements from pip freeze if dependencies.txt doesn't exist
        try:
            result = subprocess.run(["pip", "freeze"], capture_output=True, text=True)
            with open(package_path / "requirements.txt", "w") as f:
                f.write(result.stdout)
            logger.info("Generated requirements.txt from pip freeze")
        except Exception as e:
            logger.error(f"Failed to generate requirements.txt: {e}")
    
    # Create the ZIP archive
    zip_filename = f"{package_name}.zip"
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(package_path):
            for file in files:
                file_path = os.path.join(root, file)
                zipf.write(file_path, os.path.relpath(file_path, package_path.parent))
    
    # Clean up the temporary directory
    shutil.rmtree(package_path)
    
    logger.info(f"Package created successfully: {zip_filename}")
    return zip_filename

if __name__ == "__main__":
    try:
        zip_file = create_v503_package()
        print(f"Successfully created package: {zip_file}")
    except Exception as e:
        logger.error(f"Error creating package: {e}")
        print(f"Error creating package: {e}")
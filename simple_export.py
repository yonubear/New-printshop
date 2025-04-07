"""
Simple Export Script for Print Shop Management System

This script creates a directory with essential files for deployment:
1. Application code and templates
2. Configuration templates
3. Documentation files
"""

import os
import shutil
import datetime
import zipfile

def simple_export():
    """Create a simple export package with essential files"""
    # Create timestamp for directory name
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    output_dir = f"printshop_export_{timestamp}"
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"Creating export package in {output_dir}...")
    
    # Essential files to include in the export
    essential_files = [
        # Python application files
        'main.py', 'app.py', 'models.py', 'routes.py', 
        'email_service.py', 'nextcloud_client.py', 'pdf_generator.py',
        'create_admin_user.py', 'export_db.py', 'import_db.py',
        
        # Configuration and documentation
        '.env.template', 'dependencies.txt', 'README.md', 'SETUP_GUIDE.md',
        
        # Export tools
        'export_db.py', 'import_db.py', 'export_files.py'
    ]
    
    # Essential directories to include in the export
    essential_dirs = [
        'static', 'templates'
    ]
    
    # Copy essential files
    for filename in essential_files:
        if os.path.exists(filename):
            shutil.copy2(filename, os.path.join(output_dir, filename))
            print(f"Copied file: {filename}")
    
    # Copy essential directories
    for dirname in essential_dirs:
        if os.path.exists(dirname) and os.path.isdir(dirname):
            shutil.copytree(dirname, os.path.join(output_dir, dirname))
            print(f"Copied directory: {dirname}")
    
    # Create a deployment guide
    deploy_guide_path = os.path.join(output_dir, 'DEPLOYMENT.md')
    with open(deploy_guide_path, 'w') as f:
        f.write("# Print Shop Management System Deployment Guide\n\n")
        f.write("This export package contains everything needed to deploy the Print Shop Management System "
                "to your own server with Nextcloud integration.\n\n")
        f.write("## Quick Start\n\n")
        f.write("1. Extract this package to your server\n")
        f.write("2. Follow the instructions in `SETUP_GUIDE.md` to configure the application\n")
        f.write("3. Create a virtual environment and install dependencies:\n\n")
        f.write("```bash\n")
        f.write("python -m venv venv\n")
        f.write("source venv/bin/activate  # On Windows: venv\\Scripts\\activate\n")
        f.write("pip install -r dependencies.txt\n")
        f.write("```\n\n")
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
        for root, dirs, files in os.walk(output_dir):
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
    simple_export()
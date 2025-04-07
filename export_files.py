"""
Export files from Nextcloud to local directory
This utility downloads all files from Nextcloud to a local directory for backup or migration.
"""
import os
import argparse
import datetime
import zipfile
from dotenv import load_dotenv
from nextcloud_client import NextcloudClient

# Load environment variables
load_dotenv()

def export_files(output_dir=None, create_zip=False):
    """
    Export files from Nextcloud to local directory
    
    Args:
        output_dir: Directory to save files to. If None, a timestamped directory is created.
        create_zip: Whether to create a ZIP archive of the files
    
    Returns:
        Path to the output directory or ZIP file
    """
    # Get Nextcloud configuration from environment
    nextcloud_url = os.environ.get('NEXTCLOUD_URL')
    nextcloud_username = os.environ.get('NEXTCLOUD_USERNAME')
    nextcloud_password = os.environ.get('NEXTCLOUD_PASSWORD')
    nextcloud_folder = os.environ.get('NEXTCLOUD_FOLDER', 'print_orders')
    
    # Check if Nextcloud is configured
    if not (nextcloud_url and nextcloud_username and nextcloud_password):
        print("Error: Nextcloud is not configured. Set NEXTCLOUD_URL, NEXTCLOUD_USERNAME, and NEXTCLOUD_PASSWORD environment variables.")
        return None
    
    # Create output directory if not provided
    if not output_dir:
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        output_dir = f"nextcloud_export_{timestamp}"
    
    # Create directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Connect to Nextcloud
    try:
        client = NextcloudClient(
            nextcloud_url,
            nextcloud_username,
            nextcloud_password,
            nextcloud_folder
        )
        
        # List files in Nextcloud
        files = client.list_files()
        
        if not files:
            print("No files found in Nextcloud")
            return output_dir
        
        # Download each file
        for file_info in files:
            file_path = file_info.get('path', '')
            file_name = os.path.basename(file_path)
            
            # Skip directories
            if file_path.endswith('/'):
                continue
            
            print(f"Downloading {file_path}...")
            
            # Create local directory structure if needed
            rel_path = file_path
            if rel_path.startswith('/'):
                rel_path = rel_path[1:]
            
            local_path = os.path.join(output_dir, rel_path)
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            
            # Download file
            temp_path = client.download_file(file_path)
            
            # Move temporary file to final location
            with open(temp_path, 'rb') as src, open(local_path, 'wb') as dst:
                dst.write(src.read())
            
            # Clean up temporary file
            os.unlink(temp_path)
        
        # Create ZIP archive if requested
        if create_zip:
            zip_path = f"{output_dir}.zip"
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, _, files in os.walk(output_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, output_dir)
                        zipf.write(file_path, arcname)
            
            print(f"Files exported to {zip_path}")
            return zip_path
        
        print(f"Files exported to {output_dir}")
        return output_dir
        
    except Exception as e:
        print(f"Error exporting files: {str(e)}")
        return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Export files from Nextcloud')
    parser.add_argument('--output', '-o', help='Output directory')
    parser.add_argument('--zip', '-z', action='store_true', help='Create ZIP archive')
    args = parser.parse_args()
    
    export_files(args.output, args.zip)
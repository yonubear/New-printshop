"""
Nextcloud Delete Diagnostic Tool

This script tests file deletion in your Nextcloud server configuration.
It will create a test file, then attempt to delete it, logging all steps.
"""
import os
import logging
import tempfile
import sys
from io import BytesIO

from nextcloud_client import NextcloudClient

# Set up logging
logging.basicConfig(level=logging.DEBUG, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('nextcloud_delete_test')

def run_delete_test():
    """Run a comprehensive deletion test"""
    # Get Nextcloud configuration from environment
    nextcloud_url = os.environ.get('NEXTCLOUD_URL')
    nextcloud_username = os.environ.get('NEXTCLOUD_USERNAME')
    nextcloud_password = os.environ.get('NEXTCLOUD_PASSWORD')
    nextcloud_folder = os.environ.get('NEXTCLOUD_FOLDER', 'print_orders')
    
    if not all([nextcloud_url, nextcloud_username, nextcloud_password]):
        logger.error("Missing Nextcloud configuration. Please set all environment variables.")
        return False
    
    logger.info(f"Testing Nextcloud configuration: URL={nextcloud_url}, "
                f"Username={nextcloud_username}, Folder={nextcloud_folder}")
    
    # Create Nextcloud client
    nextcloud = NextcloudClient(
        nextcloud_url, 
        nextcloud_username, 
        nextcloud_password, 
        nextcloud_folder
    )
    
    # Test file path
    test_file_path = f"test_delete_{os.urandom(4).hex()}.txt"
    
    # Create test content
    test_content = f"Test file for deletion testing - {os.urandom(4).hex()}"
    test_file = BytesIO(test_content.encode('utf-8'))
    
    # Step 1: Upload test file
    logger.info(f"Step 1: Uploading test file to {test_file_path}")
    upload_success = nextcloud.upload_file(test_file, test_file_path)
    
    if not upload_success:
        logger.error("Failed to upload test file. Aborting test.")
        return False
    
    logger.info("Upload successful!")
    
    # Step 2: List files to confirm upload
    logger.info("Step 2: Listing files to confirm upload")
    files = nextcloud.list_files()
    
    if test_file_path not in files:
        logger.warning(f"Test file {test_file_path} not found in file listing, but upload reported success.")
    else:
        logger.info(f"Test file confirmed in file listing: {test_file_path}")
    
    # Step 3: Delete test file
    logger.info(f"Step 3: Deleting test file {test_file_path}")
    delete_success = nextcloud.delete_file(test_file_path)
    
    if delete_success:
        logger.info("Delete operation reported success!")
    else:
        logger.error("Delete operation failed!")
        
    # Step 4: List files again to confirm deletion
    logger.info("Step 4: Listing files to confirm deletion")
    files_after = nextcloud.list_files()
    
    if test_file_path in files_after:
        logger.error(f"Test file {test_file_path} still exists after deletion operation!")
        return False
    else:
        logger.info(f"Test file {test_file_path} successfully deleted and no longer appears in file listing.")
    
    return delete_success

if __name__ == "__main__":
    logger.info("Starting Nextcloud deletion test")
    success = False
    try:
        success = run_delete_test()
        if success:
            logger.info("✅ Nextcloud deletion test completed successfully!")
            print("\nSUCCESS: The Nextcloud deletion functionality is working correctly!")
        else:
            logger.error("❌ Nextcloud deletion test failed!")
            print("\nFAILURE: The Nextcloud deletion functionality is not working correctly.")
            print("Please check the logs above for more details.")
    except Exception as e:
        logger.exception("Unexpected error during test")
        print(f"\nERROR: An unexpected error occurred: {str(e)}")
    
    sys.exit(0 if success else 1)
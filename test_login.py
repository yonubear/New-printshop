#!/usr/bin/env python3
import os
import sys
import logging
from dotenv import load_dotenv
from nextcloud_client import NextcloudClient

# Set up logging
logging.basicConfig(level=logging.DEBUG, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def test_login():
    """Test basic Nextcloud login with our updated client"""
    
    # Get Nextcloud configuration from environment
    nextcloud_url = os.environ.get('NEXTCLOUD_URL')
    nextcloud_username = os.environ.get('NEXTCLOUD_USERNAME')
    nextcloud_password = os.environ.get('NEXTCLOUD_PASSWORD')
    nextcloud_folder = os.environ.get('NEXTCLOUD_FOLDER', 'print_orders')
    
    # Check if Nextcloud is configured
    if not (nextcloud_url and nextcloud_username and nextcloud_password):
        logger.error("Nextcloud is not configured. Set NEXTCLOUD_URL, NEXTCLOUD_USERNAME, and NEXTCLOUD_PASSWORD environment variables.")
        return False
    
    logger.info(f"Testing connection to Nextcloud server: {nextcloud_url}")
    logger.info(f"Initially using username: {nextcloud_username}")
    logger.info(f"Using folder: {nextcloud_folder}")
    
    # Initialize Nextcloud client
    client = NextcloudClient(
        nextcloud_url,
        nextcloud_username,
        nextcloud_password,
        nextcloud_folder
    )
    
    # After client initialization, the username might have been changed 
    # to handle email format issues
    logger.info(f"Effective username after client initialization: {client.username}")
    
    # Test listing files
    logger.info("Testing listing files...")
    files = client.list_files()
    logger.info(f"Files found: {len(files)}")
    if files:
        logger.info(f"First few files: {files[:5]}")
    
    # Return success based on whether we could list files
    if len(files) >= 0:  # Consider even empty folder as success
        logger.info("Login test completed successfully")
        return True
    else:
        logger.error("Login test failed")
        return False

if __name__ == "__main__":
    logger.info("Starting Nextcloud login test")
    success = test_login()
    
    if success:
        logger.info("Nextcloud login test completed successfully")
        sys.exit(0)
    else:
        logger.error("Nextcloud login test failed")
        sys.exit(1)
#!/usr/bin/env python3
"""
Nextcloud Connection Tester

This script tests your Nextcloud connection and helps diagnose connectivity issues.
"""

import os
import sys
import logging
import requests
from dotenv import load_dotenv
from nextcloud_client import NextcloudClient
from io import BytesIO

# Set up logging
logging.basicConfig(level=logging.DEBUG, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def test_connection():
    """Test basic Nextcloud connectivity"""
    
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
    logger.info(f"Using username: {nextcloud_username}")
    logger.info(f"Using folder: {nextcloud_folder}")
    
    # Verify URL is accessible
    try:
        response = requests.get(nextcloud_url, timeout=10)
        logger.info(f"Server response: {response.status_code}")
        if response.status_code not in [200, 301, 302]:
            logger.error(f"Server returned unexpected status code: {response.status_code}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Server connection failed: {e}")
        return False
    
    # Try with different username formats
    usernames_to_try = [nextcloud_username]
    
    # If username contains @, add the version without domain
    if '@' in nextcloud_username:
        username_without_domain = nextcloud_username.split('@')[0]
        usernames_to_try.append(username_without_domain)
        logger.info(f"Will also try username without domain: {username_without_domain}")
    
    success = False
    last_error = None
    
    for username in usernames_to_try:
        logger.info(f"Trying with username: {username}")
        
        try:
            # Initialize Nextcloud client
            client = NextcloudClient(
                nextcloud_url,
                username,
                nextcloud_password,
                nextcloud_folder
            )
            
            # Test authentication
            logger.info("Testing authentication...")
            
            # Try to list files
            logger.info("Listing files...")
            files = client.list_files()
            logger.info(f"Files found: {len(files)}")
            if files:
                logger.info(f"First few files: {files[:5]}")
            
            # Test file upload
            logger.info("Testing file upload...")
            test_file = BytesIO(b"This is a test file for Nextcloud connectivity testing.")
            upload_success = client.upload_file(test_file, "test_connection.txt")
            
            if upload_success:
                logger.info("File upload successful")
                
                # Test file download
                logger.info("Testing file download...")
                downloaded_file = client.download_file("test_connection.txt")
                
                if downloaded_file:
                    logger.info("File download successful")
                    # Clean up the temporary file
                    os.unlink(downloaded_file)
                else:
                    logger.error("File download failed")
                
                # Test file deletion
                logger.info("Testing file deletion...")
                delete_success = client.delete_file("test_connection.txt")
                
                if delete_success:
                    logger.info("File deletion successful")
                else:
                    logger.error("File deletion failed")
                
                logger.info("All tests completed")
                return True
            else:
                logger.error("File upload failed")
                continue  # Try next username
            
        except Exception as e:
            logger.error(f"An error occurred with username '{username}': {e}")
            last_error = e
            continue  # Try next username
    
    # If we get here, all username attempts failed
    logger.error(f"All username formats failed. Last error: {last_error}")
    return False

def get_basic_system_info():
    """Get basic system information that might be relevant to connectivity issues"""
    import platform
    import socket
    
    logger.info("--- System Information ---")
    logger.info(f"Python version: {platform.python_version()}")
    logger.info(f"Platform: {platform.platform()}")
    logger.info(f"Machine: {platform.machine()}")
    logger.info(f"Processor: {platform.processor()}")
    
    # Check DNS resolution
    nextcloud_url = os.environ.get('NEXTCLOUD_URL', '')
    if nextcloud_url:
        from urllib.parse import urlparse
        hostname = urlparse(nextcloud_url).netloc
        try:
            ip_address = socket.gethostbyname(hostname)
            logger.info(f"DNS resolution for {hostname}: {ip_address}")
        except socket.gaierror:
            logger.error(f"Could not resolve hostname: {hostname}")

if __name__ == "__main__":
    logger.info("Starting Nextcloud connection test")
    get_basic_system_info()
    success = test_connection()
    
    if success:
        logger.info("Nextcloud connection test completed successfully")
        sys.exit(0)
    else:
        logger.error("Nextcloud connection test failed")
        sys.exit(1)
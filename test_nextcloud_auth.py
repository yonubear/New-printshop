"""
Simple Nextcloud Authentication Test

This script performs a simple test to check if the Nextcloud authentication is working.
It tries to list files in the root directory of your Nextcloud account.
"""
import os
import logging
import sys
import requests
from requests.auth import HTTPBasicAuth

# Set up logging
logging.basicConfig(level=logging.DEBUG, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('nextcloud_auth_test')

def test_auth():
    """Test Nextcloud authentication by listing files in the root directory"""
    # Get credentials from environment variables
    url = os.environ.get('NEXTCLOUD_URL')
    username = os.environ.get('NEXTCLOUD_USERNAME')
    password = os.environ.get('NEXTCLOUD_PASSWORD')
    
    logger.info(f"Testing Nextcloud authentication with: URL={url}, Username={username}")
    
    if not all([url, username, password]):
        logger.error("Missing Nextcloud configuration. Please check environment variables.")
        return False
    
    # Try to list files in the root directory
    auth = HTTPBasicAuth(username, password)
    webdav_url = f"{url}/remote.php/dav/files/{username}/"
    
    try:
        logger.info(f"Making request to: {webdav_url}")
        response = requests.request(
            "PROPFIND",
            webdav_url,
            auth=auth,
            headers={"Depth": "1"},
            timeout=30
        )
        
        logger.info(f"Response status code: {response.status_code}")
        logger.info(f"Response headers: {response.headers}")
        
        if response.status_code == 207:  # Multi-status response (success)
            logger.info("Authentication successful!")
            logger.info(f"Response preview: {response.text[:500]}...")
            return True
        else:
            logger.error(f"Authentication failed with status code: {response.status_code}")
            logger.error(f"Response: {response.text}")
            return False
            
    except Exception as e:
        logger.exception(f"Error during authentication test: {str(e)}")
        return False

def test_alternative_username():
    """Test with username formats both with and without @domain part"""
    # Get credentials from environment variables
    url = os.environ.get('NEXTCLOUD_URL')
    username = os.environ.get('NEXTCLOUD_USERNAME')
    password = os.environ.get('NEXTCLOUD_PASSWORD')
    
    if '@' in username:
        # Try without domain part
        alt_username = username.split('@')[0]
        logger.info(f"Original username has @ symbol: {username}")
        logger.info(f"Trying alternative username (without domain): {alt_username}")
        
        # Store original username and set alternative
        original = os.environ.get('NEXTCLOUD_USERNAME')
        os.environ['NEXTCLOUD_USERNAME'] = alt_username
        
        # Try authentication with alternative
        success = test_auth()
        
        # Restore original
        os.environ['NEXTCLOUD_USERNAME'] = original
        
        return success
    else:
        # Try with @gmail.com
        alt_username = f"{username}@gmail.com"
        logger.info(f"Original username has no @ symbol: {username}")
        logger.info(f"Trying alternative username (with domain): {alt_username}")
        
        # Store original username and set alternative
        original = os.environ.get('NEXTCLOUD_USERNAME')
        os.environ['NEXTCLOUD_USERNAME'] = alt_username
        
        # Try authentication with alternative
        success = test_auth()
        
        # Restore original
        os.environ['NEXTCLOUD_USERNAME'] = original
        
        return success

if __name__ == "__main__":
    logger.info("Starting Nextcloud authentication test...")
    
    # First test with the configured username
    success = test_auth()
    
    if not success:
        logger.info("Trying alternative username format...")
        alt_success = test_alternative_username()
        
        if alt_success:
            logger.info("✅ Authentication succeeded with alternative username format!")
            logger.info("Please update your .env file with the working username format.")
            sys.exit(0)
    else:
        logger.info("✅ Authentication succeeded with configured username!")
        sys.exit(0)
            
    logger.error("❌ Authentication failed with both username formats.")
    logger.error("Please check your Nextcloud credentials and server configuration.")
    sys.exit(1)
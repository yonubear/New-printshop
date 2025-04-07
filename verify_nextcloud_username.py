#!/usr/bin/env python3
"""
Nextcloud Username Format Verification Tool

This script helps verify the correct username format for your Nextcloud server
by testing different variations of your username.

Usage:
    python verify_nextcloud_username.py

Follow the prompts to enter your Nextcloud server URL, username, and password.
The script will try different formats of your username and report which one works.
"""

import os
import sys
import logging
import requests
from getpass import getpass
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_username_format(url, username, password):
    """Test different formats of the username to find which one works"""
    
    # Create variations of the username to test
    username_variants = [username]
    
    # If username contains @, add the part before @ as a variant
    if '@' in username:
        username_before_at = username.split('@')[0]
        username_variants.append(username_before_at)
        logger.info(f"Will also try username without domain part: {username_before_at}")
    
    # If username contains dots, add a variant without dots
    if '.' in username and '@' not in username:
        username_without_dots = username.replace('.', '')
        username_variants.append(username_without_dots)
        logger.info(f"Will also try username without dots: {username_without_dots}")
    
    results = []
    
    # Test each variant
    for variant in username_variants:
        logger.info(f"Testing username format: {variant}")
        
        # Test with WebDAV endpoint
        webdav_url = f"{url.rstrip('/')}/remote.php/dav/files/{variant}/"
        
        try:
            response = requests.request(
                "PROPFIND",
                webdav_url,
                auth=(username, password),  # Use original username for auth
                headers={"Depth": "0"},
                timeout=10
            )
            
            status = response.status_code
            logger.info(f"Status code: {status}")
            
            if status == 207:  # Multi-Status (success)
                results.append({
                    "username": variant,
                    "works": True,
                    "status": status,
                    "message": "Success! This username format works."
                })
                logger.info(f"✓ Username '{variant}' works correctly!")
            else:
                error_msg = "Unknown error"
                if "not found" in response.text:
                    error_msg = "Username not found on server"
                elif "Unauthorized" in response.text:
                    error_msg = "Authentication failed"
                
                results.append({
                    "username": variant,
                    "works": False,
                    "status": status,
                    "message": error_msg
                })
                logger.info(f"✗ Username '{variant}' failed with status {status}: {error_msg}")
                
        except Exception as e:
            logger.error(f"Error testing username '{variant}': {e}")
            results.append({
                "username": variant,
                "works": False,
                "status": 0,
                "message": str(e)
            })
    
    return results

def main():
    """Main function to run the verification tool"""
    logger.info("Nextcloud Username Format Verification Tool")
    logger.info("------------------------------------------")
    
    # Load existing settings from .env file if available
    load_dotenv()
    default_url = os.environ.get('NEXTCLOUD_URL', '')
    default_username = os.environ.get('NEXTCLOUD_USERNAME', '')
    
    # Get Nextcloud details from user
    print("\nPlease enter your Nextcloud details:")
    url = input(f"Nextcloud URL {f'[{default_url}]' if default_url else ''}: ").strip() or default_url
    username = input(f"Nextcloud username {f'[{default_username}]' if default_username else ''}: ").strip() or default_username
    password = getpass("Nextcloud password: ")
    
    if not (url and username and password):
        logger.error("URL, username, and password are all required")
        return 1
    
    print("\nTesting different username formats...")
    results = test_username_format(url, username, password)
    
    # Display results
    print("\nResults:")
    print("========")
    
    working_format = None
    for result in results:
        status_symbol = "✓" if result["works"] else "✗"
        print(f"{status_symbol} {result['username']} - {result['message']}")
        
        if result["works"]:
            working_format = result["username"]
    
    # Provide recommendation
    print("\nRecommendation:")
    print("==============")
    
    if working_format:
        print(f"Use this username format in your .env file: {working_format}")
        
        # If the working format is different from what's in .env
        if working_format != default_username and default_username:
            print("\nTo update your .env file, replace:")
            print(f"NEXTCLOUD_USERNAME={default_username}")
            print("with:")
            print(f"NEXTCLOUD_USERNAME={working_format}")
    else:
        print("None of the tested username formats worked.")
        print("Recommendations:")
        print("1. Check that your Nextcloud server URL is correct")
        print("2. Verify your password is correct")
        print("3. Confirm the account exists on the Nextcloud server")
        print("4. Try logging in through the web interface and check what username is shown in the URL")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
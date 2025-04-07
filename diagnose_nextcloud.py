#!/usr/bin/env python3
"""
Nextcloud Diagnostic Tool

This script performs detailed diagnostics of your Nextcloud configuration and attempts
to identify and fix common issues with file uploads.
"""

import os
import sys
import logging
import requests
import json
from dotenv import load_dotenv
from io import BytesIO
from urllib.parse import urlparse
import xml.etree.ElementTree as ET

# Set up verbose logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class NextcloudDiagnostic:
    def __init__(self):
        # Get Nextcloud configuration from environment
        self.nextcloud_url = os.environ.get('NEXTCLOUD_URL', '')
        self.nextcloud_username = os.environ.get('NEXTCLOUD_USERNAME', '')
        self.nextcloud_password = os.environ.get('NEXTCLOUD_PASSWORD', '')
        self.nextcloud_folder = os.environ.get('NEXTCLOUD_FOLDER', 'print_orders')
        
        # Parsed URL components
        if self.nextcloud_url:
            self.parsed_url = urlparse(self.nextcloud_url)
            self.hostname = self.parsed_url.netloc
        else:
            self.parsed_url = None
            self.hostname = None
        
        # Auth object for requests
        self.auth = (self.nextcloud_username, self.nextcloud_password) if self.nextcloud_username and self.nextcloud_password else None
        
        # Test results
        self.results = {
            "config_check": None,
            "server_reachable": None,
            "auth_valid": None,
            "webdav_available": None,
            "folder_exists": None,
            "folder_writable": None,
            "file_upload": None,
            "file_download": None,
            "file_delete": None,
            "errors": []
        }
    
    def check_config(self):
        """Check if configuration is complete"""
        logger.info("Checking Nextcloud configuration...")
        
        if not self.nextcloud_url:
            self.results["errors"].append("NEXTCLOUD_URL environment variable is not set")
            self.results["config_check"] = False
            return False
            
        if not self.nextcloud_username:
            self.results["errors"].append("NEXTCLOUD_USERNAME environment variable is not set")
            self.results["config_check"] = False
            return False
            
        if not self.nextcloud_password:
            self.results["errors"].append("NEXTCLOUD_PASSWORD environment variable is not set")
            self.results["config_check"] = False
            return False
        
        logger.info(f"Nextcloud URL: {self.nextcloud_url}")
        logger.info(f"Nextcloud username: {self.nextcloud_username}")
        logger.info(f"Nextcloud folder: {self.nextcloud_folder}")
        
        self.results["config_check"] = True
        return True
    
    def check_server_reachable(self):
        """Check if Nextcloud server is reachable"""
        logger.info(f"Checking if server {self.nextcloud_url} is reachable...")
        
        try:
            response = requests.get(
                self.nextcloud_url, 
                timeout=10,
                verify=True  # Change to False if using self-signed certificates
            )
            
            status_code = response.status_code
            logger.info(f"Server responded with status code: {status_code}")
            
            if status_code in [200, 301, 302]:
                self.results["server_reachable"] = True
                return True
            else:
                self.results["errors"].append(f"Server returned unexpected status code: {status_code}")
                self.results["server_reachable"] = False
                return False
                
        except requests.exceptions.SSLError as e:
            logger.error(f"SSL verification failed: {e}")
            self.results["errors"].append(f"SSL verification failed: {e}")
            self.results["server_reachable"] = False
            
            # Suggest possible solutions
            logger.warning("This could be due to a self-signed certificate or an expired certificate.")
            logger.warning("Try setting verify=False in the requests.get() call if using self-signed certificates.")
            
            return False
            
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error: {e}")
            self.results["errors"].append(f"Connection error: {e}")
            self.results["server_reachable"] = False
            return False
            
        except requests.exceptions.Timeout as e:
            logger.error(f"Connection timed out: {e}")
            self.results["errors"].append(f"Connection timed out: {e}")
            self.results["server_reachable"] = False
            return False
            
        except Exception as e:
            logger.error(f"Unexpected error checking server: {e}")
            self.results["errors"].append(f"Unexpected error checking server: {e}")
            self.results["server_reachable"] = False
            return False
    
    def check_authentication(self):
        """Check if authentication credentials are valid"""
        logger.info("Checking authentication...")
        
        try:
            # Try to access the status.php endpoint, which requires authentication
            url = f"{self.nextcloud_url}/status.php"
            response = requests.get(
                url, 
                auth=self.auth,
                timeout=10
            )
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    logger.info(f"Authentication successful. Nextcloud version: {data.get('version', 'unknown')}")
                    self.results["auth_valid"] = True
                    return True
                except json.JSONDecodeError:
                    logger.warning("Response was not valid JSON, but authentication seems to work")
                    self.results["auth_valid"] = True
                    return True
            else:
                logger.error(f"Authentication failed with status code: {response.status_code}")
                self.results["errors"].append(f"Authentication failed with status code: {response.status_code}")
                self.results["auth_valid"] = False
                return False
                
        except Exception as e:
            logger.error(f"Authentication check failed: {e}")
            self.results["errors"].append(f"Authentication check failed: {e}")
            self.results["auth_valid"] = False
            return False
    
    def check_webdav_available(self):
        """Check if WebDAV API is available"""
        logger.info("Checking WebDAV availability...")
        
        # Try both username formats - with domain and without domain
        usernames_to_try = [self.nextcloud_username]
        
        # If username contains @, add the version without domain
        if '@' in self.nextcloud_username:
            username_without_domain = self.nextcloud_username.split('@')[0]
            usernames_to_try.append(username_without_domain)
            logger.info(f"Will also try username without domain: {username_without_domain}")
        
        for username in usernames_to_try:
            try:
                url = f"{self.nextcloud_url}/remote.php/dav/files/{username}/"
                logger.info(f"Trying WebDAV with username: {username}")
                
                response = requests.request(
                    "PROPFIND",
                    url,
                    auth=self.auth,
                    headers={"Depth": "0"},
                    timeout=10
                )
                
                if response.status_code == 207:  # Multi-Status
                    logger.info(f"WebDAV API is available with username: {username}")
                    self.results["webdav_available"] = True
                    # Update the username to the working one for future operations
                    self.nextcloud_username = username
                    return True
                else:
                    logger.warning(f"WebDAV API check failed with username '{username}' - status code: {response.status_code}")
                    logger.debug(f"Response content: {response.text[:500]}...")
            
            except Exception as e:
                logger.warning(f"WebDAV availability check failed with username '{username}': {e}")
        
        # If we get here, all username attempts failed
        logger.error("WebDAV API not available with any username format")
        self.results["errors"].append("WebDAV API check failed with all username formats")
        self.results["webdav_available"] = False
        return False
    
    def check_folder_exists(self):
        """Check if the target folder exists or can be created"""
        logger.info(f"Checking if folder '{self.nextcloud_folder}' exists...")
        
        try:
            # By this point, check_webdav_available should have set the correct username format
            url = f"{self.nextcloud_url}/remote.php/dav/files/{self.nextcloud_username}/{self.nextcloud_folder}"
            logger.info(f"Checking folder using username: {self.nextcloud_username}")
            
            response = requests.request(
                "PROPFIND",
                url,
                auth=self.auth,
                headers={"Depth": "0"},
                timeout=10
            )
            
            if response.status_code == 207:  # Multi-Status
                logger.info(f"Folder '{self.nextcloud_folder}' exists")
                self.results["folder_exists"] = True
                return True
            elif response.status_code == 404:
                logger.info(f"Folder '{self.nextcloud_folder}' does not exist, attempting to create it...")
                
                # Try to create the folder
                response = requests.request(
                    "MKCOL",
                    url,
                    auth=self.auth,
                    timeout=10
                )
                
                if response.status_code in [201, 204]:
                    logger.info(f"Folder '{self.nextcloud_folder}' created successfully")
                    self.results["folder_exists"] = True
                    return True
                else:
                    logger.error(f"Failed to create folder with status code: {response.status_code}")
                    logger.error(f"Response content: {response.text}")
                    self.results["errors"].append(f"Failed to create folder with status code: {response.status_code}")
                    self.results["folder_exists"] = False
                    return False
            else:
                logger.error(f"Unexpected status code checking folder: {response.status_code}")
                logger.error(f"Response content: {response.text}")
                self.results["errors"].append(f"Unexpected status code checking folder: {response.status_code}")
                self.results["folder_exists"] = False
                return False
                
        except Exception as e:
            logger.error(f"Folder check failed: {e}")
            self.results["errors"].append(f"Folder check failed: {e}")
            self.results["folder_exists"] = False
            return False
    
    def check_folder_writable(self):
        """Check if the target folder is writable"""
        logger.info(f"Checking if folder '{self.nextcloud_folder}' is writable...")
        
        try:
            # Create a test file in the folder
            test_filename = "_test_write_permission.txt"
            url = f"{self.nextcloud_url}/remote.php/dav/files/{self.nextcloud_username}/{self.nextcloud_folder}/{test_filename}"
            
            file_content = "This is a test file to check write permissions."
            file_obj = BytesIO(file_content.encode())
            
            response = requests.put(
                url,
                data=file_obj,
                auth=self.auth,
                timeout=10
            )
            
            if response.status_code in [201, 204]:
                logger.info(f"Test file created successfully, folder is writable")
                
                # Clean up the test file
                delete_response = requests.delete(
                    url,
                    auth=self.auth,
                    timeout=10
                )
                
                if delete_response.status_code in [204, 404]:
                    logger.info("Test file deleted successfully")
                else:
                    logger.warning(f"Could not delete test file: {delete_response.status_code}")
                
                self.results["folder_writable"] = True
                return True
            else:
                logger.error(f"Failed to create test file with status code: {response.status_code}")
                logger.error(f"Response content: {response.text}")
                self.results["errors"].append(f"Failed to create test file with status code: {response.status_code}")
                self.results["folder_writable"] = False
                return False
                
        except Exception as e:
            logger.error(f"Write permission check failed: {e}")
            self.results["errors"].append(f"Write permission check failed: {e}")
            self.results["folder_writable"] = False
            return False
    
    def test_file_operations(self):
        """Test file upload, download, and delete operations"""
        logger.info("Testing file operations...")
        
        try:
            # Test file upload
            test_filename = "_test_file_operations.txt"
            url = f"{self.nextcloud_url}/remote.php/dav/files/{self.nextcloud_username}/{self.nextcloud_folder}/{test_filename}"
            
            file_content = "This file tests the full file operation cycle: upload, download, and delete."
            file_obj = BytesIO(file_content.encode())
            
            logger.info("Testing file upload...")
            upload_response = requests.put(
                url,
                data=file_obj,
                auth=self.auth,
                timeout=10
            )
            
            if upload_response.status_code in [201, 204]:
                logger.info("File upload successful")
                self.results["file_upload"] = True
                
                # Test file download
                logger.info("Testing file download...")
                download_response = requests.get(
                    url,
                    auth=self.auth,
                    timeout=10
                )
                
                if download_response.status_code == 200:
                    downloaded_content = download_response.text
                    logger.info(f"File download successful, content: {downloaded_content}")
                    self.results["file_download"] = True
                else:
                    logger.error(f"File download failed with status code: {download_response.status_code}")
                    self.results["errors"].append(f"File download failed with status code: {download_response.status_code}")
                    self.results["file_download"] = False
                
                # Test file delete
                logger.info("Testing file delete...")
                delete_response = requests.delete(
                    url,
                    auth=self.auth,
                    timeout=10
                )
                
                if delete_response.status_code in [204, 404]:
                    logger.info("File delete successful")
                    self.results["file_delete"] = True
                else:
                    logger.error(f"File delete failed with status code: {delete_response.status_code}")
                    self.results["errors"].append(f"File delete failed with status code: {delete_response.status_code}")
                    self.results["file_delete"] = False
                
                return True
            else:
                logger.error(f"File upload failed with status code: {upload_response.status_code}")
                logger.error(f"Response content: {upload_response.text}")
                self.results["errors"].append(f"File upload failed with status code: {upload_response.status_code}")
                self.results["file_upload"] = False
                return False
                
        except Exception as e:
            logger.error(f"File operations test failed: {e}")
            self.results["errors"].append(f"File operations test failed: {e}")
            self.results["file_upload"] = False
            return False
    
    def suggest_fixes(self):
        """Suggest fixes based on the diagnostic results"""
        logger.info("\n=== DIAGNOSTIC SUMMARY ===")
        
        all_passed = True
        
        for test, result in self.results.items():
            if test != "errors" and result is not None:
                status = "PASSED" if result else "FAILED"
                logger.info(f"{test.replace('_', ' ').title()}: {status}")
                if not result:
                    all_passed = False
        
        if all_passed:
            logger.info("\n✅ All tests passed! Your Nextcloud connection should be working correctly.")
            return
        
        logger.info("\n=== SUGGESTED FIXES ===")
        
        # Config check failed
        if self.results["config_check"] is False:
            logger.info("1. Configuration Issue:")
            logger.info("   - Check your .env file and ensure all Nextcloud variables are set")
            logger.info("   - Verify that your .env file is being loaded correctly")
            logger.info("   - Try setting the variables directly in the environment")
        
        # Server unreachable
        if self.results["server_reachable"] is False:
            logger.info("2. Server Connection Issue:")
            logger.info("   - Verify the Nextcloud URL is correct (it should include https:// or http://)")
            logger.info("   - Check if the server is running and accessible from your network")
            logger.info("   - Verify DNS resolution for the hostname")
            logger.info("   - Check if a firewall is blocking the connection")
            logger.info("   - If using SSL, make sure the certificate is valid and trusted")
        
        # Authentication failed
        if self.results["auth_valid"] is False:
            logger.info("3. Authentication Issue:")
            logger.info("   - Verify your username and password")
            logger.info("   - Try logging in to the Nextcloud web interface with the same credentials")
            logger.info("   - Check if your account is locked or disabled")
            logger.info("   - Consider creating an app password specifically for the Print Shop System")
        
        # WebDAV unavailable
        if self.results["webdav_available"] is False:
            logger.info("4. WebDAV API Issue:")
            logger.info("   - Ensure WebDAV is enabled in your Nextcloud instance")
            logger.info("   - Check if access to /remote.php/dav/ endpoints is restricted")
            logger.info("   - Verify that no proxy or middleware is interfering with WebDAV requests")
        
        # Folder issues
        if self.results["folder_exists"] is False:
            logger.info("5. Folder Access Issue:")
            logger.info("   - Check if the user has permission to create folders")
            logger.info("   - Try creating the folder manually through the web interface")
            logger.info("   - Check for any special characters in the folder name that might cause issues")
        
        # Write permission issues
        if self.results["folder_writable"] is False:
            logger.info("6. Write Permission Issue:")
            logger.info("   - Verify that the user has write permissions to the folder")
            logger.info("   - Check if the server's disk space is full")
            logger.info("   - Check if there are any quota limitations for the user")
        
        # File upload issues
        if self.results["file_upload"] is False:
            logger.info("7. File Upload Issue:")
            logger.info("   - Check if the file size is within the allowed limits")
            logger.info("   - Verify that the folder path is correct")
            logger.info("   - Check for any file name restrictions")
            logger.info("   - Look for specific error messages in the server logs")
    
    def run_diagnostics(self):
        """Run all diagnostic tests"""
        if not self.check_config():
            logger.error("Configuration check failed. Fix configuration issues and try again.")
            self.suggest_fixes()
            return False
        
        if not self.check_server_reachable():
            logger.error("Server unreachable. Fix connection issues and try again.")
            self.suggest_fixes()
            return False
        
        if not self.check_authentication():
            logger.error("Authentication failed. Fix authentication issues and try again.")
            self.suggest_fixes()
            return False
        
        if not self.check_webdav_available():
            logger.error("WebDAV API not available. Fix WebDAV issues and try again.")
            self.suggest_fixes()
            return False
        
        self.check_folder_exists()
        self.check_folder_writable()
        self.test_file_operations()
        
        self.suggest_fixes()
        
        # Return True if all critical tests passed
        return (self.results["config_check"] and 
                self.results["server_reachable"] and 
                self.results["auth_valid"] and 
                self.results["webdav_available"] and 
                self.results["folder_exists"] and 
                self.results["folder_writable"] and 
                self.results["file_upload"])


if __name__ == "__main__":
    print("Running Nextcloud diagnostic tool...")
    print("This will test your Nextcloud connection and configuration.")
    print("For more information, see NEXTCLOUD_TROUBLESHOOTING.md\n")
    
    diagnostic = NextcloudDiagnostic()
    success = diagnostic.run_diagnostics()
    
    if success:
        print("\nDiagnostic completed successfully.")
        sys.exit(0)
    else:
        print("\nDiagnostic failed. Please fix the issues and try again.")
        sys.exit(1)
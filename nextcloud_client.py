import os
import requests
import tempfile
import logging
import time
from io import BytesIO
from requests.auth import HTTPBasicAuth
from urllib.parse import urlparse

class NextcloudClient:
    def __init__(self, base_url, username, password, root_folder):
        self.base_url = base_url.rstrip('/') if base_url else ""
        self.username = username
        self.password = password
        self.root_folder = root_folder
        self.auth = HTTPBasicAuth(username, password)
        
        # Set up enhanced logging
        self.logger = logging.getLogger(__name__)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.DEBUG)
        
        # Validate configuration
        if not base_url:
            self.logger.error("Nextcloud base URL is not configured")
        if not username or not password:
            self.logger.error("Nextcloud credentials are not configured")
        
        # Try to check if we should use a different username format
        self._try_alternative_username_format()
            
        # Retry configuration
        self.max_retries = 3
        self.retry_delay = 1  # second
        
    def _try_alternative_username_format(self):
        """
        Some Nextcloud instances don't recognize email-format usernames.
        Try to determine if we should use a username without the domain part.
        """
        # Don't do any automatic username transformations
        # Use exactly what's in the environment variable
        self.logger.info(f"Using configured username: {self.username}")
        return

    def _ensure_folder_exists(self, folder_path):
        """
        Ensure that the given folder path exists in Nextcloud
        Handles nested folder creation if necessary
        """
        if not folder_path:
            return True
            
        # First ensure the root folder exists
        root_url = f"{self.base_url}/remote.php/dav/files/{self.username}/{self.root_folder}"
        
        try:
            response = requests.request(
                "PROPFIND",
                root_url,
                auth=self.auth,
                headers={"Depth": "0"},
                timeout=10
            )
            
            # If root folder doesn't exist, create it
            if response.status_code == 404:
                self.logger.debug(f"Creating root folder: {self.root_folder}")
                response = requests.request(
                    "MKCOL",
                    root_url,
                    auth=self.auth,
                    timeout=10
                )
                
                if response.status_code not in [201, 204]:
                    self.logger.error(f"Failed to create root folder: {response.status_code} - {response.text}")
                    return False
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Network error checking root folder: {str(e)}")
            return False
        
        # Split the folder path into components to create each level if needed
        path_components = folder_path.split('/')
        current_path = ""
        
        for component in path_components:
            if not component:  # Skip empty components
                continue
                
            if current_path:
                current_path = f"{current_path}/{component}"
            else:
                current_path = component
                
            folder_url = f"{self.base_url}/remote.php/dav/files/{self.username}/{self.root_folder}/{current_path}"
            
            try:
                # Check if this folder level exists
                response = requests.request(
                    "PROPFIND",
                    folder_url,
                    auth=self.auth,
                    headers={"Depth": "0"},
                    timeout=10
                )
                
                # If folder doesn't exist, create it
                if response.status_code == 404:
                    self.logger.debug(f"Creating folder: {current_path}")
                    response = requests.request(
                        "MKCOL",
                        folder_url,
                        auth=self.auth,
                        timeout=10
                    )
                    
                    if response.status_code not in [201, 204]:
                        self.logger.error(f"Failed to create folder {current_path}: "
                                         f"{response.status_code} - {response.text}")
                        return False
                        
            except requests.exceptions.RequestException as e:
                self.logger.error(f"Network error creating folder {current_path}: {str(e)}")
                return False
                
        return True

    def upload_file(self, file_obj, file_path):
        """Upload a file to Nextcloud with retry capability"""
        # Check if configuration is valid
        if not self.base_url or not self.username or not self.password:
            self.logger.error("Nextcloud not properly configured. Cannot upload file.")
            return False
            
        # Extract folder path from file path
        folder_path = os.path.dirname(file_path)
        
        # Ensure folder exists
        if folder_path and not self._ensure_folder_exists(folder_path):
            self.logger.error(f"Failed to create or access folder: {folder_path}")
            return False
        
        # Prepare for upload
        url = f"{self.base_url}/remote.php/dav/files/{self.username}/{self.root_folder}/{file_path}"
        self.logger.debug(f"Uploading file to: {url}")
        
        # Implement retry logic
        for attempt in range(1, self.max_retries + 1):
            try:
                # Reset file pointer to beginning for each attempt
                file_obj.seek(0)
                
                # Get file size for logging
                file_obj.seek(0, os.SEEK_END)
                file_size = file_obj.tell()
                file_obj.seek(0)
                
                self.logger.debug(f"Attempt {attempt}/{self.max_retries}: "
                                 f"Uploading file {file_path} ({file_size} bytes)")
                
                # Upload with timeout to prevent hanging
                response = requests.put(
                    url,
                    data=file_obj,
                    auth=self.auth,
                    timeout=30,  # 30 second timeout
                    headers={
                        'Content-Type': 'application/octet-stream'
                    }
                )
                
                if response.status_code in [201, 204]:
                    self.logger.debug(f"File uploaded successfully: {file_path}")
                    return True
                else:
                    error_msg = f"Failed to upload file (Attempt {attempt}/{self.max_retries}): " \
                               f"Status {response.status_code} - {response.text}"
                    self.logger.error(error_msg)
                    
                    # Check for specific error codes to determine if retry is appropriate
                    if response.status_code in [400, 401, 403, 404, 409, 413]:
                        # Client errors that won't be resolved by retrying
                        self.logger.error(f"Not retrying due to client error status code: {response.status_code}")
                        return False
                        
                    # For other errors, retry after delay
                    if attempt < self.max_retries:
                        delay = self.retry_delay * (2 ** (attempt - 1))  # Exponential backoff
                        self.logger.info(f"Retrying after {delay} seconds...")
                        time.sleep(delay)
                    
            except requests.exceptions.RequestException as e:
                self.logger.error(f"Network error during upload (Attempt {attempt}/{self.max_retries}): {str(e)}")
                
                # For connection errors, retry after delay
                if attempt < self.max_retries:
                    delay = self.retry_delay * (2 ** (attempt - 1))  # Exponential backoff
                    self.logger.info(f"Retrying after {delay} seconds...")
                    time.sleep(delay)
        
        self.logger.error(f"Failed to upload file after {self.max_retries} attempts")
        return False

    def download_file(self, file_path):
        """Download a file from Nextcloud and return a temporary file path"""
        url = f"{self.base_url}/remote.php/dav/files/{self.username}/{self.root_folder}/{file_path}"
        
        self.logger.debug(f"Downloading file from: {url}")
        
        response = requests.get(
            url,
            auth=self.auth,
            stream=True
        )
        
        if response.status_code == 200:
            # Create a temporary file
            temp_file = tempfile.NamedTemporaryFile(delete=False)
            
            # Write the file content to the temporary file
            for chunk in response.iter_content(chunk_size=8192):
                temp_file.write(chunk)
                
            temp_file.close()
            
            self.logger.debug(f"File downloaded successfully: {file_path}")
            return temp_file.name
        else:
            self.logger.error(f"Failed to download file: {response.status_code} - {response.text}")
            return None

    def delete_file(self, file_path):
        """Delete a file from Nextcloud"""
        url = f"{self.base_url}/remote.php/dav/files/{self.username}/{self.root_folder}/{file_path}"
        
        self.logger.debug(f"Deleting file: {url}")
        self.logger.debug(f"Using auth: username={self.username}, password=******")
        
        try:
            response = requests.delete(
                url,
                auth=self.auth,
                timeout=30  # Add timeout to prevent hanging
            )
            
            if response.status_code in [204, 404]:  # 204 = Success, 404 = Already gone
                self.logger.debug(f"File deleted successfully: {file_path}")
                return True
            else:
                # Enhanced logging for troubleshooting
                self.logger.error(f"Failed to delete file: {file_path}")
                self.logger.error(f"Status code: {response.status_code}")
                self.logger.error(f"Response text: {response.text}")
                
                # Check for specific error conditions
                if response.status_code == 403:
                    self.logger.error("Permission denied - check Nextcloud user permissions")
                elif response.status_code == 401:
                    self.logger.error("Authentication failed - check credentials")
                elif response.status_code == 423:
                    self.logger.error("Resource is locked - file may be in use")
                    
                return False
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Network error during file deletion: {str(e)}")
            return False

    def list_files(self, folder_path=""):
        """List files in a folder"""
        url = f"{self.base_url}/remote.php/dav/files/{self.username}/{self.root_folder}/{folder_path}"
        
        response = requests.request(
            "PROPFIND",
            url,
            auth=self.auth,
            headers={"Depth": "1"}
        )
        
        if response.status_code == 207:  # Multi-status response
            # This is a simplified parsing of the XML response
            # For production, use a proper XML parser
            files = []
            for line in response.text.split("<d:href>"):
                if "remote.php/dav/files" in line:
                    file_path = line.split("</d:href>")[0]
                    file_name = file_path.split("/")[-1]
                    if file_name:  # Skip the current directory entry
                        files.append(file_name)
            
            self.logger.debug(f"Files in {folder_path}: {files}")
            return files
        else:
            self.logger.error(f"Failed to list files: {response.status_code} - {response.text}")
            return []

    def get_preview_url(self, file_path):
        """Get a preview URL for a file (for images, PDFs, etc.)"""
        return f"{self.base_url}/index.php/apps/files/ajax/preview.php?file=/{self.root_folder}/{file_path}&x=1024&y=1024&a=true&t={self.username}"

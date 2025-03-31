import os
import requests
import tempfile
import logging
from io import BytesIO
from requests.auth import HTTPBasicAuth

class NextcloudClient:
    def __init__(self, base_url, username, password, root_folder):
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self.root_folder = root_folder
        self.auth = HTTPBasicAuth(username, password)
        self.logger = logging.getLogger(__name__)

    def _ensure_folder_exists(self, folder_path):
        """Ensure that the given folder path exists in Nextcloud"""
        url = f"{self.base_url}/remote.php/dav/files/{self.username}/{self.root_folder}/{folder_path}"
        
        # First check if folder exists
        response = requests.request(
            "PROPFIND",
            url,
            auth=self.auth
        )
        
        # If folder doesn't exist, create it
        if response.status_code == 404:
            self.logger.debug(f"Creating folder: {folder_path}")
            response = requests.request(
                "MKCOL",
                url,
                auth=self.auth
            )
            
            if response.status_code not in [201, 204]:
                self.logger.error(f"Failed to create folder: {response.status_code} - {response.text}")
                return False
                
        return True

    def upload_file(self, file_obj, file_path):
        """Upload a file to Nextcloud"""
        # Extract folder path from file path
        folder_path = os.path.dirname(file_path)
        
        # Ensure folder exists
        if folder_path and not self._ensure_folder_exists(folder_path):
            return False
        
        # Reset file pointer to beginning
        file_obj.seek(0)
        
        # Upload file
        url = f"{self.base_url}/remote.php/dav/files/{self.username}/{self.root_folder}/{file_path}"
        
        self.logger.debug(f"Uploading file to: {url}")
        
        response = requests.put(
            url,
            data=file_obj,
            auth=self.auth
        )
        
        if response.status_code in [201, 204]:
            self.logger.debug(f"File uploaded successfully: {file_path}")
            return True
        else:
            self.logger.error(f"Failed to upload file: {response.status_code} - {response.text}")
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
        
        response = requests.delete(
            url,
            auth=self.auth
        )
        
        if response.status_code in [204, 404]:  # 204 = Success, 404 = Already gone
            self.logger.debug(f"File deleted successfully: {file_path}")
            return True
        else:
            self.logger.error(f"Failed to delete file: {response.status_code} - {response.text}")
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

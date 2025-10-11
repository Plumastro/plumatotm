"""
Google Drive Uploader Module for PLUMASTRO
Handles uploading birth charts and radar charts to Google Drive
"""

import os
import io
from google.oauth2 import service_account
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseUpload
from googleapiclient.errors import HttpError

class GoogleDriveUploader:
    """
    Handles file uploads to Google Drive with folder management
    Supports both Service Account and OAuth 2.0 authentication
    """
    
    # Google Drive folder ID (PLUMASTRO_Orders folder)
    PARENT_FOLDER_ID = '1eLDMyqLwP5MZLzjEQHFgnuVxDn9zao_L'
    
    # Scopes required for Google Drive API
    SCOPES = ['https://www.googleapis.com/auth/drive.file']
    
    def __init__(self, token_path='google_drive_token.json', service_account_path='google_drive_credentials.json'):
        """
        Initialize Google Drive uploader
        
        Args:
            token_path: Path to OAuth token JSON (preferred for personal Drive)
            service_account_path: Path to service account JSON (fallback, requires Shared Drive)
        """
        self.token_path = token_path
        self.service_account_path = service_account_path
        self.service = None
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Google Drive API using OAuth or Service Account"""
        try:
            # Try OAuth from environment variable first (for production)
            token_from_env = os.environ.get('GOOGLE_DRIVE_TOKEN')
            if token_from_env:
                print("[INFO] Using OAuth authentication from environment variable...")
                import json
                token_data = json.loads(token_from_env)
                creds = Credentials.from_authorized_user_info(token_data, self.SCOPES)
                self.service = build('drive', 'v3', credentials=creds)
                print("[OK] Google Drive authentication successful (OAuth from env)")
            # Try OAuth from file (for local development)
            elif os.path.exists(self.token_path):
                print("[INFO] Using OAuth authentication from file...")
                creds = Credentials.from_authorized_user_file(self.token_path, self.SCOPES)
                self.service = build('drive', 'v3', credentials=creds)
                print("[OK] Google Drive authentication successful (OAuth from file)")
            # Fallback to Service Account (requires Shared Drive)
            elif os.path.exists(self.service_account_path):
                print("[INFO] Using Service Account authentication...")
                credentials = service_account.Credentials.from_service_account_file(
                    self.service_account_path,
                    scopes=self.SCOPES
                )
                self.service = build('drive', 'v3', credentials=credentials)
                print("[OK] Google Drive authentication successful (Service Account)")
                print("[WARN] Service Accounts require Shared Drives for uploads")
            else:
                raise FileNotFoundError(
                    f"No credentials found. Expected:\n"
                    f"  - GOOGLE_DRIVE_TOKEN environment variable (production)\n"
                    f"  - {self.token_path} (OAuth file, local development)\n"
                    f"  - {self.service_account_path} (Service Account, requires Shared Drive)\n"
                    f"Run 'python setup_google_drive_oauth.py' to set up OAuth."
                )
        except Exception as e:
            print(f"[ERROR] Google Drive authentication failed: {e}")
            raise
    
    def find_folder_by_name(self, folder_name, parent_folder_id=None):
        """
        Find a folder by name in Google Drive
        
        Args:
            folder_name: Name of the folder to find
            parent_folder_id: ID of parent folder to search in
            
        Returns:
            Folder ID if found, None otherwise
        """
        try:
            if parent_folder_id:
                query = f"name='{folder_name}' and '{parent_folder_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
            else:
                query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
            
            results = self.service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name)',
                pageSize=1
            ).execute()
            
            files = results.get('files', [])
            if files:
                print(f"[FOUND] Existing folder: {folder_name} (ID: {files[0]['id']})")
                return files[0]['id']
            return None
        except HttpError as error:
            print(f"[ERROR] Error finding folder: {error}")
            return None
    
    def create_folder(self, folder_name, parent_folder_id=None):
        """
        Create a new folder in Google Drive
        
        Args:
            folder_name: Name of the folder to create
            parent_folder_id: ID of parent folder (optional)
            
        Returns:
            Folder ID of created folder
        """
        try:
            file_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            
            if parent_folder_id:
                file_metadata['parents'] = [parent_folder_id]
            
            folder = self.service.files().create(
                body=file_metadata,
                fields='id'
            ).execute()
            
            print(f"[OK] Created folder: {folder_name} (ID: {folder.get('id')})")
            return folder.get('id')
        except HttpError as error:
            print(f"[ERROR] Error creating folder: {error}")
            raise
    
    def get_or_create_folder(self, folder_name, parent_folder_id=None):
        """
        Get existing folder or create new one
        
        Args:
            folder_name: Name of the folder
            parent_folder_id: ID of parent folder (optional)
            
        Returns:
            Folder ID
        """
        folder_id = self.find_folder_by_name(folder_name, parent_folder_id)
        if folder_id:
            return folder_id
        return self.create_folder(folder_name, parent_folder_id)
    
    def find_file_in_folder(self, filename, folder_id):
        """
        Find a file by name in a specific folder
        
        Args:
            filename: Name of the file to find
            folder_id: ID of the folder to search in
            
        Returns:
            File ID if found, None otherwise
        """
        try:
            query = f"name='{filename}' and '{folder_id}' in parents and trashed=false"
            
            results = self.service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name)',
                pageSize=1
            ).execute()
            
            files = results.get('files', [])
            if files:
                return files[0]['id']
            return None
        except HttpError as error:
            print(f"[ERROR] Error finding file: {error}")
            return None
    
    def upload_file(self, file_path, folder_id, filename=None):
        """
        Upload a file to Google Drive (create new or update existing)
        
        Args:
            file_path: Path to the file to upload
            folder_id: ID of the folder to upload to
            filename: Custom filename (optional, uses file_path basename if not provided)
            
        Returns:
            File ID of uploaded file
        """
        try:
            if not os.path.exists(file_path):
                print(f"[WARN] File not found: {file_path}")
                return None
            
            if filename is None:
                filename = os.path.basename(file_path)
            
            # Check if file already exists
            existing_file_id = self.find_file_in_folder(filename, folder_id)
            
            # Prepare file metadata
            file_metadata = {'name': filename}
            
            # Determine MIME type
            mime_type = 'image/png' if filename.endswith('.png') else 'application/octet-stream'
            
            media = MediaFileUpload(file_path, mimetype=mime_type, resumable=True)
            
            if existing_file_id:
                # Update existing file
                file = self.service.files().update(
                    fileId=existing_file_id,
                    media_body=media
                ).execute()
                print(f"[UPDATE] Updated file: {filename} (ID: {file.get('id')})")
            else:
                # Create new file
                file_metadata['parents'] = [folder_id]
                file = self.service.files().create(
                    body=file_metadata,
                    media_body=media,
                    fields='id'
                ).execute()
                print(f"[OK] Uploaded file: {filename} (ID: {file.get('id')})")
            
            return file.get('id')
        except HttpError as error:
            print(f"[ERROR] Error uploading file {filename}: {error}")
            return None
    
    def upload_order_files(self, order_name_nb, birth_chart_path, radar1_path, radar2_path, radar3_path, prompt_chatgpt_path=None):
        """
        Upload all files for an order to Google Drive
        
        Args:
            order_name_nb: Order name/number (e.g., "#1050-1")
            birth_chart_path: Path to birth chart PNG
            radar1_path: Path to radar chart 1 PNG
            radar2_path: Path to radar chart 2 PNG
            radar3_path: Path to radar chart 3 PNG
            prompt_chatgpt_path: Path to prompt_chatgpt.txt (optional)
            
        Returns:
            dict: Results with folder_id, folder_url and uploaded file IDs
        """
        print(f"\n[UPLOAD] Starting Google Drive upload for order: {order_name_nb}")
        
        try:
            # Get or create order folder
            order_folder_id = self.get_or_create_folder(order_name_nb, self.PARENT_FOLDER_ID)
            
            # Generate folder URL
            folder_url = f"https://drive.google.com/drive/folders/{order_folder_id}"
            
            results = {
                'order_folder_id': order_folder_id,
                'folder_url': folder_url,
                'uploaded_files': {}
            }
            
            # Upload files
            files_to_upload = {
                'birth_chart.png': birth_chart_path,
                'radar1.png': radar1_path,
                'radar2.png': radar2_path,
                'radar3.png': radar3_path
            }
            
            # Add prompt_chatgpt.txt if provided
            if prompt_chatgpt_path:
                files_to_upload['prompt_chatgpt.txt'] = prompt_chatgpt_path
            
            for filename, file_path in files_to_upload.items():
                if file_path and os.path.exists(file_path):
                    file_id = self.upload_file(file_path, order_folder_id, filename)
                    results['uploaded_files'][filename] = file_id
                else:
                    print(f"[WARN] Skipping {filename}: file not found at {file_path}")
                    results['uploaded_files'][filename] = None
            
            print(f"[OK] Google Drive upload completed for order: {order_name_nb}")
            print(f"[FOLDER] URL: {folder_url}")
            
            return results
            
        except Exception as e:
            print(f"[ERROR] Error uploading order files: {e}")
            import traceback
            traceback.print_exc()
            return None


# Convenience function for easy import
def upload_order_to_drive(order_name_nb, birth_chart_path, radar1_path, radar2_path, radar3_path, prompt_chatgpt_path=None):
    """
    Convenience function to upload order files to Google Drive
    
    Args:
        order_name_nb: Order name/number (e.g., "#1050-1")
        birth_chart_path: Path to birth chart PNG
        radar1_path: Path to radar chart 1 PNG
        radar2_path: Path to radar chart 2 PNG
        radar3_path: Path to radar chart 3 PNG
        prompt_chatgpt_path: Path to prompt_chatgpt.txt (optional)
        
    Returns:
        dict: Upload results or None if failed
    """
    try:
        uploader = GoogleDriveUploader()
        return uploader.upload_order_files(
            order_name_nb,
            birth_chart_path,
            radar1_path,
            radar2_path,
            radar3_path,
            prompt_chatgpt_path
        )
    except Exception as e:
        print(f"[ERROR] Failed to upload to Google Drive: {e}")
        return None


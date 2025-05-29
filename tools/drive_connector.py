"""
Google Drive connector for DeepResearch system.
Provides OAuth authorization and file access capabilities.
"""

import os
import json
import pickle
from typing import Dict, Any, List, Optional, Union, IO
from dataclasses import dataclass
from datetime import datetime

from utils.logger import LoggerMixin


@dataclass
class DriveFile:
    """Represents a Google Drive file."""
    id: str
    name: str
    mime_type: str
    size: Optional[int] = None
    created_time: Optional[datetime] = None
    modified_time: Optional[datetime] = None
    parents: Optional[List[str]] = None
    web_view_link: Optional[str] = None
    download_url: Optional[str] = None


@dataclass
class DriveOperationResult:
    """Result of Drive operation."""
    success: bool
    operation: str
    data: Any = None
    error: Optional[str] = None
    file_info: Optional[DriveFile] = None


class GoogleDriveConnector(LoggerMixin):
    """
    Google Drive connector with OAuth2 authentication.
    Provides file listing, reading, and basic operations.
    """
    
    def __init__(self, credentials_file: str = "credentials.json", token_file: str = "token.pickle"):
        """
        Initialize Google Drive connector.
        
        Args:
            credentials_file: Path to OAuth2 credentials file
            token_file: Path to store access token
        """
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.service = None
        self.credentials = None
        
        # Required scopes for Drive access
        self.scopes = [
            'https://www.googleapis.com/auth/drive.readonly',
            'https://www.googleapis.com/auth/drive.file'
        ]
        
        # Check if Google API client is available
        try:
            import googleapiclient
            import google_auth_oauthlib
            import google.auth
            self.google_api_available = True
        except ImportError:
            self.google_api_available = False
            self.log_warning("Google API client not available. Drive operations will be disabled.")
    
    def authenticate(self) -> bool:
        """
        Authenticate with Google Drive API.
        
        Returns:
            True if authentication successful
        """
        if not self.google_api_available:
            self.log_error("Google API client not available")
            return False
        
        try:
            from google.auth.transport.requests import Request
            from google_auth_oauthlib.flow import InstalledAppFlow
            from googleapiclient.discovery import build
            
            creds = None
            
            # Load existing token
            if os.path.exists(self.token_file):
                with open(self.token_file, 'rb') as token:
                    creds = pickle.load(token)
            
            # If no valid credentials, get new ones
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    # Refresh expired token
                    creds.refresh(Request())
                else:
                    # Get new token
                    if not os.path.exists(self.credentials_file):
                        self.log_error(f"Credentials file not found: {self.credentials_file}")
                        return False
                    
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_file, self.scopes
                    )
                    creds = flow.run_local_server(port=0)
                
                # Save credentials for next run
                with open(self.token_file, 'wb') as token:
                    pickle.dump(creds, token)
            
            # Build service
            self.service = build('drive', 'v3', credentials=creds)
            self.credentials = creds
            
            self.log_info("Google Drive authentication successful")
            return True
            
        except Exception as e:
            self.log_error(f"Google Drive authentication failed: {e}")
            return False
    
    def list_files(
        self, 
        folder_id: Optional[str] = None,
        query: Optional[str] = None,
        max_results: int = 100
    ) -> DriveOperationResult:
        """
        List files in Google Drive.
        
        Args:
            folder_id: Optional folder ID to list files from
            query: Optional search query
            max_results: Maximum number of results
        
        Returns:
            Drive operation result with file list
        """
        if not self.service:
            if not self.authenticate():
                return DriveOperationResult(
                    success=False,
                    operation="list_files",
                    error="Authentication failed"
                )
        
        try:
            # Build query
            search_query = ""
            if folder_id:
                search_query = f"'{folder_id}' in parents"
            if query:
                if search_query:
                    search_query += f" and ({query})"
                else:
                    search_query = query
            
            # Add filter to exclude trashed files
            if search_query:
                search_query += " and trashed=false"
            else:
                search_query = "trashed=false"
            
            # Execute request
            results = self.service.files().list(
                q=search_query,
                pageSize=max_results,
                fields="nextPageToken, files(id, name, mimeType, size, createdTime, modifiedTime, parents, webViewLink)"
            ).execute()
            
            items = results.get('files', [])
            
            # Convert to DriveFile objects
            drive_files = []
            for item in items:
                drive_file = DriveFile(
                    id=item['id'],
                    name=item['name'],
                    mime_type=item['mimeType'],
                    size=int(item.get('size', 0)) if item.get('size') else None,
                    created_time=datetime.fromisoformat(item['createdTime'].replace('Z', '+00:00')) if item.get('createdTime') else None,
                    modified_time=datetime.fromisoformat(item['modifiedTime'].replace('Z', '+00:00')) if item.get('modifiedTime') else None,
                    parents=item.get('parents', []),
                    web_view_link=item.get('webViewLink')
                )
                drive_files.append(drive_file)
            
            self.log_info(f"Listed {len(drive_files)} files from Google Drive")
            
            return DriveOperationResult(
                success=True,
                operation="list_files",
                data={
                    "files": drive_files,
                    "count": len(drive_files),
                    "query": search_query
                }
            )
            
        except Exception as e:
            self.log_error(f"Failed to list Drive files: {e}")
            return DriveOperationResult(
                success=False,
                operation="list_files",
                error=str(e)
            )
    
    def get_file_info(self, file_id: str) -> DriveOperationResult:
        """
        Get information about a specific file.
        
        Args:
            file_id: Google Drive file ID
        
        Returns:
            Drive operation result with file info
        """
        if not self.service:
            if not self.authenticate():
                return DriveOperationResult(
                    success=False,
                    operation="get_file_info",
                    error="Authentication failed"
                )
        
        try:
            file_metadata = self.service.files().get(
                fileId=file_id,
                fields="id, name, mimeType, size, createdTime, modifiedTime, parents, webViewLink"
            ).execute()
            
            drive_file = DriveFile(
                id=file_metadata['id'],
                name=file_metadata['name'],
                mime_type=file_metadata['mimeType'],
                size=int(file_metadata.get('size', 0)) if file_metadata.get('size') else None,
                created_time=datetime.fromisoformat(file_metadata['createdTime'].replace('Z', '+00:00')) if file_metadata.get('createdTime') else None,
                modified_time=datetime.fromisoformat(file_metadata['modifiedTime'].replace('Z', '+00:00')) if file_metadata.get('modifiedTime') else None,
                parents=file_metadata.get('parents', []),
                web_view_link=file_metadata.get('webViewLink')
            )
            
            return DriveOperationResult(
                success=True,
                operation="get_file_info",
                data=file_metadata,
                file_info=drive_file
            )
            
        except Exception as e:
            self.log_error(f"Failed to get file info for {file_id}: {e}")
            return DriveOperationResult(
                success=False,
                operation="get_file_info",
                error=str(e)
            )
    
    def download_file(self, file_id: str, local_path: Optional[str] = None) -> DriveOperationResult:
        """
        Download a file from Google Drive.
        
        Args:
            file_id: Google Drive file ID
            local_path: Optional local path to save file
        
        Returns:
            Drive operation result with file content or path
        """
        if not self.service:
            if not self.authenticate():
                return DriveOperationResult(
                    success=False,
                    operation="download_file",
                    error="Authentication failed"
                )
        
        try:
            # Get file metadata first
            file_info_result = self.get_file_info(file_id)
            if not file_info_result.success:
                return file_info_result
            
            file_info = file_info_result.file_info
            
            # Handle Google Docs, Sheets, Slides (export as different format)
            if file_info.mime_type.startswith('application/vnd.google-apps'):
                return self._export_google_doc(file_id, file_info, local_path)
            
            # Download regular files
            request = self.service.files().get_media(fileId=file_id)
            
            if local_path:
                # Download to file
                import io
                from googleapiclient.http import MediaIoBaseDownload
                
                with open(local_path, 'wb') as fh:
                    downloader = MediaIoBaseDownload(fh, request)
                    done = False
                    while done is False:
                        status, done = downloader.next_chunk()
                
                self.log_info(f"Downloaded file to {local_path}")
                
                return DriveOperationResult(
                    success=True,
                    operation="download_file",
                    data={"local_path": local_path, "size": os.path.getsize(local_path)},
                    file_info=file_info
                )
            else:
                # Return content in memory
                content = request.execute()
                
                return DriveOperationResult(
                    success=True,
                    operation="download_file",
                    data={"content": content, "size": len(content)},
                    file_info=file_info
                )
                
        except Exception as e:
            self.log_error(f"Failed to download file {file_id}: {e}")
            return DriveOperationResult(
                success=False,
                operation="download_file",
                error=str(e)
            )
    
    def _export_google_doc(self, file_id: str, file_info: DriveFile, local_path: Optional[str] = None) -> DriveOperationResult:
        """Export Google Docs/Sheets/Slides to downloadable format."""
        
        # Determine export format based on file type
        export_formats = {
            'application/vnd.google-apps.document': 'text/plain',  # Google Docs -> Text
            'application/vnd.google-apps.spreadsheet': 'text/csv',  # Google Sheets -> CSV
            'application/vnd.google-apps.presentation': 'text/plain',  # Google Slides -> Text
        }
        
        export_mime_type = export_formats.get(file_info.mime_type, 'text/plain')
        
        try:
            request = self.service.files().export_media(
                fileId=file_id,
                mimeType=export_mime_type
            )
            
            if local_path:
                # Download to file
                import io
                from googleapiclient.http import MediaIoBaseDownload
                
                with open(local_path, 'wb') as fh:
                    downloader = MediaIoBaseDownload(fh, request)
                    done = False
                    while done is False:
                        status, done = downloader.next_chunk()
                
                return DriveOperationResult(
                    success=True,
                    operation="export_google_doc",
                    data={"local_path": local_path, "export_format": export_mime_type},
                    file_info=file_info
                )
            else:
                # Return content
                content = request.execute()
                
                return DriveOperationResult(
                    success=True,
                    operation="export_google_doc",
                    data={"content": content.decode('utf-8'), "export_format": export_mime_type},
                    file_info=file_info
                )
                
        except Exception as e:
            self.log_error(f"Failed to export Google Doc {file_id}: {e}")
            return DriveOperationResult(
                success=False,
                operation="export_google_doc",
                error=str(e)
            )
    
    def read_text_file(self, file_id: str) -> DriveOperationResult:
        """
        Read text content from a file.
        
        Args:
            file_id: Google Drive file ID
        
        Returns:
            Drive operation result with text content
        """
        download_result = self.download_file(file_id)
        
        if not download_result.success:
            return download_result
        
        try:
            content = download_result.data.get("content", b"")
            
            # Try to decode as text
            if isinstance(content, bytes):
                # Try different encodings
                for encoding in ['utf-8', 'utf-16', 'latin-1']:
                    try:
                        text_content = content.decode(encoding)
                        break
                    except UnicodeDecodeError:
                        continue
                else:
                    # If all encodings fail, use utf-8 with error handling
                    text_content = content.decode('utf-8', errors='replace')
            else:
                text_content = str(content)
            
            return DriveOperationResult(
                success=True,
                operation="read_text_file",
                data={
                    "text_content": text_content,
                    "length": len(text_content),
                    "encoding": "utf-8"
                },
                file_info=download_result.file_info
            )
            
        except Exception as e:
            self.log_error(f"Failed to read text from file {file_id}: {e}")
            return DriveOperationResult(
                success=False,
                operation="read_text_file",
                error=str(e)
            )
    
    def search_files(self, search_term: str, file_type: Optional[str] = None) -> DriveOperationResult:
        """
        Search for files in Google Drive.
        
        Args:
            search_term: Search term
            file_type: Optional file type filter (e.g., 'document', 'spreadsheet')
        
        Returns:
            Drive operation result with search results
        """
        # Build search query
        query = f"name contains '{search_term}'"
        
        if file_type:
            type_mapping = {
                'document': 'application/vnd.google-apps.document',
                'spreadsheet': 'application/vnd.google-apps.spreadsheet',
                'presentation': 'application/vnd.google-apps.presentation',
                'pdf': 'application/pdf',
                'text': 'text/plain'
            }
            
            mime_type = type_mapping.get(file_type.lower())
            if mime_type:
                query += f" and mimeType='{mime_type}'"
        
        return self.list_files(query=query)
    
    def get_folder_contents(self, folder_id: str) -> DriveOperationResult:
        """
        Get contents of a specific folder.
        
        Args:
            folder_id: Google Drive folder ID
        
        Returns:
            Drive operation result with folder contents
        """
        return self.list_files(folder_id=folder_id)
    
    def create_folder(self, name: str, parent_id: Optional[str] = None) -> DriveOperationResult:
        """
        Create a new folder in Google Drive.
        
        Args:
            name: Folder name
            parent_id: Optional parent folder ID
        
        Returns:
            Drive operation result with folder info
        """
        if not self.service:
            if not self.authenticate():
                return DriveOperationResult(
                    success=False,
                    operation="create_folder",
                    error="Authentication failed"
                )
        
        try:
            file_metadata = {
                'name': name,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            
            if parent_id:
                file_metadata['parents'] = [parent_id]
            
            folder = self.service.files().create(
                body=file_metadata,
                fields='id, name, mimeType, createdTime, parents'
            ).execute()
            
            drive_folder = DriveFile(
                id=folder['id'],
                name=folder['name'],
                mime_type=folder['mimeType'],
                created_time=datetime.fromisoformat(folder['createdTime'].replace('Z', '+00:00')),
                parents=folder.get('parents', [])
            )
            
            self.log_info(f"Created folder '{name}' with ID: {folder['id']}")
            
            return DriveOperationResult(
                success=True,
                operation="create_folder",
                data=folder,
                file_info=drive_folder
            )
            
        except Exception as e:
            self.log_error(f"Failed to create folder '{name}': {e}")
            return DriveOperationResult(
                success=False,
                operation="create_folder",
                error=str(e)
            )
    
    def upload_file(self, local_path: str, name: Optional[str] = None, parent_id: Optional[str] = None) -> DriveOperationResult:
        """
        Upload a file to Google Drive.
        
        Args:
            local_path: Path to local file
            name: Optional name for uploaded file
            parent_id: Optional parent folder ID
        
        Returns:
            Drive operation result with upload info
        """
        if not self.service:
            if not self.authenticate():
                return DriveOperationResult(
                    success=False,
                    operation="upload_file",
                    error="Authentication failed"
                )
        
        if not os.path.exists(local_path):
            return DriveOperationResult(
                success=False,
                operation="upload_file",
                error=f"Local file not found: {local_path}"
            )
        
        try:
            from googleapiclient.http import MediaFileUpload
            
            file_name = name or os.path.basename(local_path)
            
            file_metadata = {'name': file_name}
            if parent_id:
                file_metadata['parents'] = [parent_id]
            
            media = MediaFileUpload(local_path, resumable=True)
            
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, name, mimeType, size, createdTime, parents, webViewLink'
            ).execute()
            
            drive_file = DriveFile(
                id=file['id'],
                name=file['name'],
                mime_type=file['mimeType'],
                size=int(file.get('size', 0)) if file.get('size') else None,
                created_time=datetime.fromisoformat(file['createdTime'].replace('Z', '+00:00')),
                parents=file.get('parents', []),
                web_view_link=file.get('webViewLink')
            )
            
            self.log_info(f"Uploaded file '{file_name}' with ID: {file['id']}")
            
            return DriveOperationResult(
                success=True,
                operation="upload_file",
                data=file,
                file_info=drive_file
            )
            
        except Exception as e:
            self.log_error(f"Failed to upload file '{local_path}': {e}")
            return DriveOperationResult(
                success=False,
                operation="upload_file",
                error=str(e)
            )
    
    def is_authenticated(self) -> bool:
        """Check if connector is authenticated."""
        return self.service is not None and self.credentials is not None
    
    def get_quota_info(self) -> DriveOperationResult:
        """Get Drive storage quota information."""
        if not self.service:
            if not self.authenticate():
                return DriveOperationResult(
                    success=False,
                    operation="get_quota_info",
                    error="Authentication failed"
                )
        
        try:
            about = self.service.about().get(fields="storageQuota").execute()
            quota = about.get('storageQuota', {})
            
            return DriveOperationResult(
                success=True,
                operation="get_quota_info",
                data={
                    "limit": int(quota.get('limit', 0)),
                    "usage": int(quota.get('usage', 0)),
                    "usage_in_drive": int(quota.get('usageInDrive', 0)),
                    "usage_in_drive_trash": int(quota.get('usageInDriveTrash', 0))
                }
            )
            
        except Exception as e:
            self.log_error(f"Failed to get quota info: {e}")
            return DriveOperationResult(
                success=False,
                operation="get_quota_info",
                error=str(e)
            ) 
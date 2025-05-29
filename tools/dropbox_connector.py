"""
Dropbox connector for DeepResearch system.
Provides OAuth authorization and file access capabilities.
"""

import os
import json
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from datetime import datetime

from utils.logger import LoggerMixin


@dataclass
class DropboxFile:
    """Represents a Dropbox file."""
    path: str
    name: str
    size: Optional[int] = None
    modified_time: Optional[datetime] = None
    is_folder: bool = False
    content_hash: Optional[str] = None
    shared_link: Optional[str] = None


@dataclass
class DropboxOperationResult:
    """Result of Dropbox operation."""
    success: bool
    operation: str
    data: Any = None
    error: Optional[str] = None
    file_info: Optional[DropboxFile] = None


class DropboxConnector(LoggerMixin):
    """
    Dropbox connector with OAuth2 authentication.
    Provides file listing, reading, and basic operations.
    """
    
    def __init__(self, app_key: str = None, app_secret: str = None, access_token: str = None):
        """
        Initialize Dropbox connector.
        
        Args:
            app_key: Dropbox app key
            app_secret: Dropbox app secret
            access_token: Optional pre-existing access token
        """
        self.app_key = app_key
        self.app_secret = app_secret
        self.access_token = access_token
        self.client = None
        
        # Check if Dropbox SDK is available
        try:
            import dropbox
            self.dropbox_available = True
        except ImportError:
            self.dropbox_available = False
            self.log_warning("Dropbox SDK not available. Dropbox operations will be disabled.")
    
    def authenticate(self, access_token: Optional[str] = None) -> bool:
        """
        Authenticate with Dropbox API.
        
        Args:
            access_token: Optional access token to use
        
        Returns:
            True if authentication successful
        """
        if not self.dropbox_available:
            self.log_error("Dropbox SDK not available")
            return False
        
        try:
            import dropbox
            
            token = access_token or self.access_token
            if not token:
                self.log_error("No access token provided")
                return False
            
            self.client = dropbox.Dropbox(token)
            
            # Test authentication by getting account info
            account_info = self.client.users_get_current_account()
            self.log_info(f"Dropbox authentication successful for: {account_info.email}")
            
            return True
            
        except Exception as e:
            self.log_error(f"Dropbox authentication failed: {e}")
            return False
    
    def get_authorization_url(self) -> Optional[str]:
        """
        Get OAuth2 authorization URL for manual authentication.
        
        Returns:
            Authorization URL or None if failed
        """
        if not self.dropbox_available:
            return None
        
        try:
            import dropbox
            
            if not self.app_key:
                self.log_error("App key required for authorization")
                return None
            
            auth_flow = dropbox.DropboxOAuth2FlowNoRedirect(
                self.app_key, 
                consumer_secret=self.app_secret,
                token_access_type='offline'
            )
            
            authorize_url = auth_flow.start()
            self.log_info(f"Authorization URL: {authorize_url}")
            
            return authorize_url
            
        except Exception as e:
            self.log_error(f"Failed to get authorization URL: {e}")
            return None
    
    def complete_authorization(self, authorization_code: str) -> Optional[str]:
        """
        Complete OAuth2 authorization flow.
        
        Args:
            authorization_code: Authorization code from user
        
        Returns:
            Access token or None if failed
        """
        if not self.dropbox_available:
            return None
        
        try:
            import dropbox
            
            auth_flow = dropbox.DropboxOAuth2FlowNoRedirect(
                self.app_key,
                consumer_secret=self.app_secret,
                token_access_type='offline'
            )
            
            oauth_result = auth_flow.finish(authorization_code)
            access_token = oauth_result.access_token
            
            self.access_token = access_token
            self.log_info("Authorization completed successfully")
            
            return access_token
            
        except Exception as e:
            self.log_error(f"Failed to complete authorization: {e}")
            return None
    
    def list_files(self, path: str = "", recursive: bool = False) -> DropboxOperationResult:
        """
        List files in Dropbox.
        
        Args:
            path: Path to list files from (empty for root)
            recursive: Whether to list files recursively
        
        Returns:
            Dropbox operation result with file list
        """
        if not self.client:
            if not self.authenticate():
                return DropboxOperationResult(
                    success=False,
                    operation="list_files",
                    error="Authentication failed"
                )
        
        try:
            if recursive:
                # Use files_list_folder with recursive=True
                result = self.client.files_list_folder(path, recursive=True)
            else:
                # List only immediate children
                result = self.client.files_list_folder(path)
            
            dropbox_files = []
            
            # Process initial results
            for entry in result.entries:
                dropbox_file = self._convert_to_dropbox_file(entry)
                dropbox_files.append(dropbox_file)
            
            # Handle pagination
            while result.has_more:
                result = self.client.files_list_folder_continue(result.cursor)
                for entry in result.entries:
                    dropbox_file = self._convert_to_dropbox_file(entry)
                    dropbox_files.append(dropbox_file)
            
            self.log_info(f"Listed {len(dropbox_files)} files from Dropbox path: {path}")
            
            return DropboxOperationResult(
                success=True,
                operation="list_files",
                data={
                    "files": dropbox_files,
                    "count": len(dropbox_files),
                    "path": path,
                    "recursive": recursive
                }
            )
            
        except Exception as e:
            self.log_error(f"Failed to list Dropbox files: {e}")
            return DropboxOperationResult(
                success=False,
                operation="list_files",
                error=str(e)
            )
    
    def get_file_info(self, path: str) -> DropboxOperationResult:
        """
        Get information about a specific file.
        
        Args:
            path: Dropbox file path
        
        Returns:
            Dropbox operation result with file info
        """
        if not self.client:
            if not self.authenticate():
                return DropboxOperationResult(
                    success=False,
                    operation="get_file_info",
                    error="Authentication failed"
                )
        
        try:
            metadata = self.client.files_get_metadata(path)
            dropbox_file = self._convert_to_dropbox_file(metadata)
            
            return DropboxOperationResult(
                success=True,
                operation="get_file_info",
                data=metadata,
                file_info=dropbox_file
            )
            
        except Exception as e:
            self.log_error(f"Failed to get file info for {path}: {e}")
            return DropboxOperationResult(
                success=False,
                operation="get_file_info",
                error=str(e)
            )
    
    def download_file(self, path: str, local_path: Optional[str] = None) -> DropboxOperationResult:
        """
        Download a file from Dropbox.
        
        Args:
            path: Dropbox file path
            local_path: Optional local path to save file
        
        Returns:
            Dropbox operation result with file content or path
        """
        if not self.client:
            if not self.authenticate():
                return DropboxOperationResult(
                    success=False,
                    operation="download_file",
                    error="Authentication failed"
                )
        
        try:
            # Get file metadata first
            file_info_result = self.get_file_info(path)
            if not file_info_result.success:
                return file_info_result
            
            file_info = file_info_result.file_info
            
            if file_info.is_folder:
                return DropboxOperationResult(
                    success=False,
                    operation="download_file",
                    error="Cannot download folder"
                )
            
            # Download file
            metadata, response = self.client.files_download(path)
            content = response.content
            
            if local_path:
                # Save to local file
                os.makedirs(os.path.dirname(local_path), exist_ok=True)
                with open(local_path, 'wb') as f:
                    f.write(content)
                
                self.log_info(f"Downloaded file to {local_path}")
                
                return DropboxOperationResult(
                    success=True,
                    operation="download_file",
                    data={"local_path": local_path, "size": len(content)},
                    file_info=file_info
                )
            else:
                # Return content in memory
                return DropboxOperationResult(
                    success=True,
                    operation="download_file",
                    data={"content": content, "size": len(content)},
                    file_info=file_info
                )
                
        except Exception as e:
            self.log_error(f"Failed to download file {path}: {e}")
            return DropboxOperationResult(
                success=False,
                operation="download_file",
                error=str(e)
            )
    
    def read_text_file(self, path: str) -> DropboxOperationResult:
        """
        Read text content from a file.
        
        Args:
            path: Dropbox file path
        
        Returns:
            Dropbox operation result with text content
        """
        download_result = self.download_file(path)
        
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
            
            return DropboxOperationResult(
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
            self.log_error(f"Failed to read text from file {path}: {e}")
            return DropboxOperationResult(
                success=False,
                operation="read_text_file",
                error=str(e)
            )
    
    def search_files(self, query: str, max_results: int = 100) -> DropboxOperationResult:
        """
        Search for files in Dropbox.
        
        Args:
            query: Search query
            max_results: Maximum number of results
        
        Returns:
            Dropbox operation result with search results
        """
        if not self.client:
            if not self.authenticate():
                return DropboxOperationResult(
                    success=False,
                    operation="search_files",
                    error="Authentication failed"
                )
        
        try:
            import dropbox
            
            # Create search options
            search_options = dropbox.files.SearchOptions(
                max_results=max_results,
                file_status=dropbox.files.FileStatus.active
            )
            
            # Perform search
            result = self.client.files_search_v2(query, options=search_options)
            
            dropbox_files = []
            for match in result.matches:
                if hasattr(match, 'metadata') and hasattr(match.metadata, 'metadata'):
                    dropbox_file = self._convert_to_dropbox_file(match.metadata.metadata)
                    dropbox_files.append(dropbox_file)
            
            self.log_info(f"Found {len(dropbox_files)} files matching query: {query}")
            
            return DropboxOperationResult(
                success=True,
                operation="search_files",
                data={
                    "files": dropbox_files,
                    "count": len(dropbox_files),
                    "query": query
                }
            )
            
        except Exception as e:
            self.log_error(f"Failed to search files: {e}")
            return DropboxOperationResult(
                success=False,
                operation="search_files",
                error=str(e)
            )
    
    def create_folder(self, path: str) -> DropboxOperationResult:
        """
        Create a new folder in Dropbox.
        
        Args:
            path: Folder path to create
        
        Returns:
            Dropbox operation result with folder info
        """
        if not self.client:
            if not self.authenticate():
                return DropboxOperationResult(
                    success=False,
                    operation="create_folder",
                    error="Authentication failed"
                )
        
        try:
            metadata = self.client.files_create_folder_v2(path)
            dropbox_folder = self._convert_to_dropbox_file(metadata.metadata)
            
            self.log_info(f"Created folder: {path}")
            
            return DropboxOperationResult(
                success=True,
                operation="create_folder",
                data=metadata.metadata,
                file_info=dropbox_folder
            )
            
        except Exception as e:
            self.log_error(f"Failed to create folder {path}: {e}")
            return DropboxOperationResult(
                success=False,
                operation="create_folder",
                error=str(e)
            )
    
    def upload_file(self, local_path: str, dropbox_path: str) -> DropboxOperationResult:
        """
        Upload a file to Dropbox.
        
        Args:
            local_path: Path to local file
            dropbox_path: Destination path in Dropbox
        
        Returns:
            Dropbox operation result with upload info
        """
        if not self.client:
            if not self.authenticate():
                return DropboxOperationResult(
                    success=False,
                    operation="upload_file",
                    error="Authentication failed"
                )
        
        if not os.path.exists(local_path):
            return DropboxOperationResult(
                success=False,
                operation="upload_file",
                error=f"Local file not found: {local_path}"
            )
        
        try:
            import dropbox
            
            file_size = os.path.getsize(local_path)
            
            with open(local_path, 'rb') as f:
                if file_size <= 150 * 1024 * 1024:  # 150MB limit for simple upload
                    # Simple upload
                    metadata = self.client.files_upload(
                        f.read(),
                        dropbox_path,
                        mode=dropbox.files.WriteMode.overwrite
                    )
                else:
                    # Chunked upload for large files
                    chunk_size = 4 * 1024 * 1024  # 4MB chunks
                    
                    # Start upload session
                    session_start_result = self.client.files_upload_session_start(
                        f.read(chunk_size)
                    )
                    cursor = dropbox.files.UploadSessionCursor(
                        session_id=session_start_result.session_id,
                        offset=f.tell()
                    )
                    
                    # Upload remaining chunks
                    while f.tell() < file_size:
                        if (file_size - f.tell()) <= chunk_size:
                            # Final chunk
                            metadata = self.client.files_upload_session_finish(
                                f.read(chunk_size),
                                cursor,
                                dropbox.files.CommitInfo(path=dropbox_path)
                            )
                        else:
                            # Intermediate chunk
                            self.client.files_upload_session_append_v2(
                                f.read(chunk_size),
                                cursor
                            )
                            cursor.offset = f.tell()
            
            dropbox_file = self._convert_to_dropbox_file(metadata)
            
            self.log_info(f"Uploaded file to {dropbox_path}")
            
            return DropboxOperationResult(
                success=True,
                operation="upload_file",
                data=metadata,
                file_info=dropbox_file
            )
            
        except Exception as e:
            self.log_error(f"Failed to upload file {local_path}: {e}")
            return DropboxOperationResult(
                success=False,
                operation="upload_file",
                error=str(e)
            )
    
    def get_shared_link(self, path: str) -> DropboxOperationResult:
        """
        Get or create a shared link for a file.
        
        Args:
            path: Dropbox file path
        
        Returns:
            Dropbox operation result with shared link
        """
        if not self.client:
            if not self.authenticate():
                return DropboxOperationResult(
                    success=False,
                    operation="get_shared_link",
                    error="Authentication failed"
                )
        
        try:
            import dropbox
            
            # Try to get existing shared link first
            try:
                shared_links = self.client.sharing_list_shared_links(path=path)
                if shared_links.links:
                    link = shared_links.links[0].url
                    return DropboxOperationResult(
                        success=True,
                        operation="get_shared_link",
                        data={"shared_link": link, "existing": True}
                    )
            except:
                pass  # No existing link, create new one
            
            # Create new shared link
            shared_link_metadata = self.client.sharing_create_shared_link_with_settings(
                path,
                settings=dropbox.sharing.SharedLinkSettings(
                    requested_visibility=dropbox.sharing.RequestedVisibility.public
                )
            )
            
            link = shared_link_metadata.url
            
            return DropboxOperationResult(
                success=True,
                operation="get_shared_link",
                data={"shared_link": link, "existing": False}
            )
            
        except Exception as e:
            self.log_error(f"Failed to get shared link for {path}: {e}")
            return DropboxOperationResult(
                success=False,
                operation="get_shared_link",
                error=str(e)
            )
    
    def _convert_to_dropbox_file(self, metadata) -> DropboxFile:
        """Convert Dropbox metadata to DropboxFile object."""
        import dropbox
        
        is_folder = isinstance(metadata, dropbox.files.FolderMetadata)
        
        return DropboxFile(
            path=metadata.path_lower,
            name=metadata.name,
            size=getattr(metadata, 'size', None) if not is_folder else None,
            modified_time=getattr(metadata, 'client_modified', None),
            is_folder=is_folder,
            content_hash=getattr(metadata, 'content_hash', None)
        )
    
    def get_account_info(self) -> DropboxOperationResult:
        """Get Dropbox account information."""
        if not self.client:
            if not self.authenticate():
                return DropboxOperationResult(
                    success=False,
                    operation="get_account_info",
                    error="Authentication failed"
                )
        
        try:
            account_info = self.client.users_get_current_account()
            space_usage = self.client.users_get_space_usage()
            
            return DropboxOperationResult(
                success=True,
                operation="get_account_info",
                data={
                    "account_id": account_info.account_id,
                    "email": account_info.email,
                    "name": account_info.name.display_name,
                    "country": account_info.country,
                    "locale": account_info.locale,
                    "space_used": space_usage.used,
                    "space_allocated": space_usage.allocation.get_individual().allocated if hasattr(space_usage.allocation, 'get_individual') else None
                }
            )
            
        except Exception as e:
            self.log_error(f"Failed to get account info: {e}")
            return DropboxOperationResult(
                success=False,
                operation="get_account_info",
                error=str(e)
            )
    
    def is_authenticated(self) -> bool:
        """Check if connector is authenticated."""
        return self.client is not None 
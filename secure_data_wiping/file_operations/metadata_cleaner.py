#!/usr/bin/env python3
"""
Metadata Cleaner Module

Provides file system metadata wiping capabilities to complement
secure file deletion operations.

This module handles the cleaning of file system metadata that might
contain traces of deleted files, enhancing the security of the
wiping process.
"""

import os
import time
import logging
from typing import Optional, Dict, Any
from pathlib import Path


class MetadataCleanerError(Exception):
    """Exception raised by metadata cleaning operations."""
    pass


class MetadataCleaner:
    """
    File system metadata cleaning for enhanced security.
    
    Provides capabilities to clean various types of metadata
    that might contain traces of deleted files:
    - File timestamps (creation, modification, access)
    - File permissions and attributes
    - Extended attributes (where supported)
    - Directory entries
    """
    
    def __init__(self):
        """Initialize the metadata cleaner."""
        self.logger = logging.getLogger(__name__)
        self.files_cleaned = 0
        self.directories_cleaned = 0
        
    def clean_file_metadata(self, file_path: str) -> bool:
        """
        Clean metadata for a file before deletion.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not os.path.exists(file_path):
                self.logger.warning(f"File not found for metadata cleaning: {file_path}")
                return False
            
            # Reset timestamps to epoch
            epoch_time = 0
            try:
                os.utime(file_path, (epoch_time, epoch_time))
                self.logger.debug(f"Reset timestamps for: {file_path}")
            except OSError as e:
                self.logger.warning(f"Could not reset timestamps for {file_path}: {e}")
            
            # Reset permissions (make writable for deletion)
            try:
                os.chmod(file_path, 0o666)
                self.logger.debug(f"Reset permissions for: {file_path}")
            except OSError as e:
                self.logger.warning(f"Could not reset permissions for {file_path}: {e}")
            
            # Clean extended attributes (Linux/macOS)
            self._clean_extended_attributes(file_path)
            
            self.files_cleaned += 1
            return True
            
        except Exception as e:
            self.logger.error(f"Metadata cleaning failed for {file_path}: {e}")
            return False
    
    def clean_directory_metadata(self, directory_path: str) -> bool:
        """
        Clean metadata for a directory.
        
        Args:
            directory_path: Path to the directory
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not os.path.exists(directory_path):
                self.logger.warning(f"Directory not found for metadata cleaning: {directory_path}")
                return False
            
            if not os.path.isdir(directory_path):
                self.logger.warning(f"Path is not a directory: {directory_path}")
                return False
            
            # Reset timestamps
            epoch_time = 0
            try:
                os.utime(directory_path, (epoch_time, epoch_time))
                self.logger.debug(f"Reset directory timestamps for: {directory_path}")
            except OSError as e:
                self.logger.warning(f"Could not reset directory timestamps for {directory_path}: {e}")
            
            # Reset permissions
            try:
                os.chmod(directory_path, 0o755)
                self.logger.debug(f"Reset directory permissions for: {directory_path}")
            except OSError as e:
                self.logger.warning(f"Could not reset directory permissions for {directory_path}: {e}")
            
            # Clean extended attributes
            self._clean_extended_attributes(directory_path)
            
            self.directories_cleaned += 1
            return True
            
        except Exception as e:
            self.logger.error(f"Directory metadata cleaning failed for {directory_path}: {e}")
            return False
    
    def _clean_extended_attributes(self, path: str):
        """
        Clean extended attributes (Linux/macOS specific).
        
        Args:
            path: Path to clean extended attributes for
        """
        try:
            # This is platform-specific functionality
            # On Linux, we could use the xattr module if available
            # On Windows, we could use alternate data streams
            # For now, we'll implement basic cross-platform functionality
            
            import platform
            system = platform.system().lower()
            
            if system == 'linux':
                self._clean_linux_xattrs(path)
            elif system == 'darwin':  # macOS
                self._clean_macos_xattrs(path)
            elif system == 'windows':
                self._clean_windows_ads(path)
            else:
                self.logger.debug(f"Extended attribute cleaning not implemented for {system}")
                
        except Exception as e:
            self.logger.debug(f"Extended attribute cleaning failed for {path}: {e}")
    
    def _clean_linux_xattrs(self, path: str):
        """Clean Linux extended attributes."""
        try:
            # Try to use xattr module if available
            try:
                import xattr
                attrs = xattr.listxattr(path)
                for attr in attrs:
                    try:
                        xattr.removexattr(path, attr)
                        self.logger.debug(f"Removed extended attribute {attr} from {path}")
                    except OSError:
                        pass  # Attribute might be system-protected
            except ImportError:
                # xattr module not available, try command line
                import subprocess
                try:
                    # List attributes
                    result = subprocess.run(['getfattr', '-n', path], 
                                          capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        # Remove all user attributes
                        subprocess.run(['setfattr', '-x', 'user.*', path], 
                                     capture_output=True, timeout=5)
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    pass  # getfattr/setfattr not available
                    
        except Exception as e:
            self.logger.debug(f"Linux xattr cleaning failed for {path}: {e}")
    
    def _clean_macos_xattrs(self, path: str):
        """Clean macOS extended attributes."""
        try:
            import subprocess
            try:
                # List attributes
                result = subprocess.run(['xattr', '-l', path], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0 and result.stdout.strip():
                    # Clear all attributes
                    subprocess.run(['xattr', '-c', path], 
                                 capture_output=True, timeout=5)
                    self.logger.debug(f"Cleared macOS extended attributes for {path}")
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass  # xattr command not available
                
        except Exception as e:
            self.logger.debug(f"macOS xattr cleaning failed for {path}: {e}")
    
    def _clean_windows_ads(self, path: str):
        """Clean Windows Alternate Data Streams."""
        try:
            # Windows ADS cleaning would require specific Windows APIs
            # For now, we'll implement basic functionality
            import subprocess
            try:
                # Use streams.exe from Sysinternals if available
                result = subprocess.run(['streams', '-s', '-d', path], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    self.logger.debug(f"Cleaned Windows ADS for {path}")
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass  # streams.exe not available
                
        except Exception as e:
            self.logger.debug(f"Windows ADS cleaning failed for {path}: {e}")
    
    def clean_file_system_journal(self, volume_path: str) -> bool:
        """
        Attempt to clean file system journal entries.
        
        Note: This is a complex operation that typically requires
        administrative privileges and is highly system-dependent.
        
        Args:
            volume_path: Path to the volume/partition
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.logger.info(f"Journal cleaning requested for volume: {volume_path}")
            
            # This is a placeholder for journal cleaning functionality
            # In a production system, this would involve:
            # - Detecting the file system type (NTFS, ext4, APFS, etc.)
            # - Using appropriate tools to clear journal entries
            # - Handling permissions and system-level access
            
            self.logger.warning("File system journal cleaning is not implemented in this version")
            self.logger.warning("For production use, consider using specialized tools like:")
            self.logger.warning("- Windows: sdelete, cipher")
            self.logger.warning("- Linux: shred, wipe, secure-delete")
            self.logger.warning("- macOS: rm -P, gshred")
            
            return False
            
        except Exception as e:
            self.logger.error(f"Journal cleaning failed for {volume_path}: {e}")
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get metadata cleaning statistics.
        
        Returns:
            Dictionary with cleaning statistics
        """
        return {
            'files_cleaned': self.files_cleaned,
            'directories_cleaned': self.directories_cleaned,
            'total_items_cleaned': self.files_cleaned + self.directories_cleaned
        }
    
    def reset_statistics(self):
        """Reset cleaning statistics."""
        self.files_cleaned = 0
        self.directories_cleaned = 0
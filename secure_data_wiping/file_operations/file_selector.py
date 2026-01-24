#!/usr/bin/env python3
"""
File Selector Module

Provides advanced file selection capabilities for the secure data wiping system.
Supports pattern-based selection, extension filtering, and various file criteria.

This module integrates with the existing system architecture while adding
granular file selection capabilities for targeted data destruction.
"""

import os
import glob
import fnmatch
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
import logging
from dataclasses import dataclass

from ..utils.data_models import WipeTarget, WipeTargetType


class FileSelectorError(Exception):
    """Exception raised by file selector operations."""
    pass


@dataclass
class FileInfo:
    """Information about a selected file."""
    path: str
    size: int
    modified_time: float
    created_time: float
    extension: str
    is_directory: bool = False
    is_accessible: bool = True
    error_message: Optional[str] = None


class FileSelector:
    """
    Advanced file selection for secure wiping operations.
    
    Provides multiple methods for selecting files based on various criteria:
    - Pattern matching (*.pdf, temp_*, etc.)
    - Extension filtering (.pdf, .docx, .xlsx)
    - Directory traversal with filtering
    - Size-based selection
    - Age-based selection
    - Content-based detection (future enhancement)
    """
    
    def __init__(self):
        """Initialize the file selector."""
        self.logger = logging.getLogger(__name__)
        self.files_scanned = 0
        self.files_selected = 0
        self.directories_scanned = 0
        
    def select_by_pattern(self, pattern: str, base_path: str = ".", recursive: bool = True) -> List[FileInfo]:
        """
        Select files matching a specific pattern.
        
        Args:
            pattern: File pattern (e.g., "*.pdf", "temp_*", "*confidential*")
            base_path: Base directory to search in
            recursive: Whether to search subdirectories
            
        Returns:
            List of FileInfo objects for matching files
            
        Raises:
            FileSelectorError: If pattern is invalid or base path doesn't exist
        """
        try:
            if not os.path.exists(base_path):
                raise FileSelectorError(f"Base path does not exist: {base_path}")
            
            if not pattern:
                raise FileSelectorError("Pattern cannot be empty")
            
            self.logger.info(f"Selecting files by pattern: {pattern} in {base_path}")
            
            files = []
            
            if recursive:
                # Use recursive glob for subdirectories
                search_pattern = os.path.join(base_path, "**", pattern)
                matched_paths = glob.glob(search_pattern, recursive=True)
            else:
                # Search only in base directory
                search_pattern = os.path.join(base_path, pattern)
                matched_paths = glob.glob(search_pattern)
            
            for file_path in matched_paths:
                if os.path.isfile(file_path):
                    file_info = self._get_file_info(file_path)
                    if file_info:
                        files.append(file_info)
                        self.files_selected += 1
                
                self.files_scanned += 1
            
            self.logger.info(f"Pattern selection complete: {len(files)} files selected")
            return files
            
        except Exception as e:
            raise FileSelectorError(f"Pattern selection failed: {e}")
    
    def select_by_extensions(self, extensions: List[str], base_path: str = ".", 
                           recursive: bool = True) -> List[FileInfo]:
        """
        Select files by file extensions.
        
        Args:
            extensions: List of extensions (e.g., ['.pdf', '.docx', '.xlsx'])
            base_path: Base directory to search in
            recursive: Whether to search subdirectories
            
        Returns:
            List of FileInfo objects for matching files
        """
        try:
            if not extensions:
                raise FileSelectorError("Extensions list cannot be empty")
            
            # Normalize extensions (ensure they start with '.')
            normalized_extensions = []
            for ext in extensions:
                if not ext.startswith('.'):
                    ext = '.' + ext
                normalized_extensions.append(ext.lower())
            
            self.logger.info(f"Selecting files by extensions: {normalized_extensions} in {base_path}")
            
            files = []
            
            for ext in normalized_extensions:
                pattern = f"*{ext}"
                ext_files = self.select_by_pattern(pattern, base_path, recursive)
                files.extend(ext_files)
            
            # Remove duplicates (in case of overlapping patterns)
            unique_files = {}
            for file_info in files:
                unique_files[file_info.path] = file_info
            
            result = list(unique_files.values())
            self.logger.info(f"Extension selection complete: {len(result)} unique files selected")
            return result
            
        except Exception as e:
            raise FileSelectorError(f"Extension selection failed: {e}")
    
    def select_directory_contents(self, directory_path: str, recursive: bool = True,
                                include_subdirs: bool = False) -> List[FileInfo]:
        """
        Select all files in a directory.
        
        Args:
            directory_path: Path to directory
            recursive: Whether to include subdirectories
            include_subdirs: Whether to include subdirectory entries themselves
            
        Returns:
            List of FileInfo objects for all files in directory
        """
        try:
            if not os.path.exists(directory_path):
                raise FileSelectorError(f"Directory does not exist: {directory_path}")
            
            if not os.path.isdir(directory_path):
                raise FileSelectorError(f"Path is not a directory: {directory_path}")
            
            self.logger.info(f"Selecting directory contents: {directory_path}")
            
            files = []
            
            if recursive:
                for root, dirs, filenames in os.walk(directory_path):
                    self.directories_scanned += 1
                    
                    # Add subdirectories if requested
                    if include_subdirs and root != directory_path:
                        dir_info = self._get_file_info(root, is_directory=True)
                        if dir_info:
                            files.append(dir_info)
                    
                    # Add files
                    for filename in filenames:
                        file_path = os.path.join(root, filename)
                        file_info = self._get_file_info(file_path)
                        if file_info:
                            files.append(file_info)
                            self.files_selected += 1
                        
                        self.files_scanned += 1
            else:
                # Only files in the immediate directory
                for item in os.listdir(directory_path):
                    item_path = os.path.join(directory_path, item)
                    if os.path.isfile(item_path):
                        file_info = self._get_file_info(item_path)
                        if file_info:
                            files.append(file_info)
                            self.files_selected += 1
                    
                    self.files_scanned += 1
            
            self.logger.info(f"Directory selection complete: {len(files)} items selected")
            return files
            
        except Exception as e:
            raise FileSelectorError(f"Directory selection failed: {e}")
    
    def select_by_size(self, min_size: Optional[int] = None, max_size: Optional[int] = None,
                      base_path: str = ".", recursive: bool = True) -> List[FileInfo]:
        """
        Select files by size criteria.
        
        Args:
            min_size: Minimum file size in bytes (None for no minimum)
            max_size: Maximum file size in bytes (None for no maximum)
            base_path: Base directory to search in
            recursive: Whether to search subdirectories
            
        Returns:
            List of FileInfo objects for files matching size criteria
        """
        try:
            if min_size is not None and min_size < 0:
                raise FileSelectorError("Minimum size cannot be negative")
            
            if max_size is not None and max_size < 0:
                raise FileSelectorError("Maximum size cannot be negative")
            
            if min_size is not None and max_size is not None and min_size > max_size:
                raise FileSelectorError("Minimum size cannot be greater than maximum size")
            
            self.logger.info(f"Selecting files by size: {min_size}-{max_size} bytes in {base_path}")
            
            # Get all files first
            all_files = self.select_by_pattern("*", base_path, recursive)
            
            # Filter by size
            filtered_files = []
            for file_info in all_files:
                if min_size is not None and file_info.size < min_size:
                    continue
                if max_size is not None and file_info.size > max_size:
                    continue
                filtered_files.append(file_info)
            
            self.logger.info(f"Size selection complete: {len(filtered_files)} files selected")
            return filtered_files
            
        except Exception as e:
            raise FileSelectorError(f"Size selection failed: {e}")
    
    def select_by_age(self, min_age_days: Optional[int] = None, max_age_days: Optional[int] = None,
                     base_path: str = ".", recursive: bool = True) -> List[FileInfo]:
        """
        Select files by age criteria.
        
        Args:
            min_age_days: Minimum file age in days (None for no minimum)
            max_age_days: Maximum file age in days (None for no maximum)
            base_path: Base directory to search in
            recursive: Whether to search subdirectories
            
        Returns:
            List of FileInfo objects for files matching age criteria
        """
        try:
            if min_age_days is not None and min_age_days < 0:
                raise FileSelectorError("Minimum age cannot be negative")
            
            if max_age_days is not None and max_age_days < 0:
                raise FileSelectorError("Maximum age cannot be negative")
            
            if min_age_days is not None and max_age_days is not None and min_age_days > max_age_days:
                raise FileSelectorError("Minimum age cannot be greater than maximum age")
            
            self.logger.info(f"Selecting files by age: {min_age_days}-{max_age_days} days in {base_path}")
            
            current_time = time.time()
            
            # Get all files first
            all_files = self.select_by_pattern("*", base_path, recursive)
            
            # Filter by age
            filtered_files = []
            for file_info in all_files:
                file_age_days = (current_time - file_info.modified_time) / (24 * 3600)
                
                if min_age_days is not None and file_age_days < min_age_days:
                    continue
                if max_age_days is not None and file_age_days > max_age_days:
                    continue
                filtered_files.append(file_info)
            
            self.logger.info(f"Age selection complete: {len(filtered_files)} files selected")
            return filtered_files
            
        except Exception as e:
            raise FileSelectorError(f"Age selection failed: {e}")
    
    def create_wipe_target(self, target_id: str, target_type: WipeTargetType, 
                          target_path: str, **kwargs) -> WipeTarget:
        """
        Create a WipeTarget from selection results.
        
        Args:
            target_id: Unique identifier for the target
            target_type: Type of wiping target
            target_path: Path to the target
            **kwargs: Additional target parameters
            
        Returns:
            WipeTarget object ready for wiping operations
        """
        try:
            return WipeTarget(
                target_id=target_id,
                target_type=target_type,
                target_path=target_path,
                **kwargs
            )
        except Exception as e:
            raise FileSelectorError(f"Failed to create wipe target: {e}")
    
    def get_selection_summary(self) -> Dict[str, Any]:
        """
        Get summary of selection operations.
        
        Returns:
            Dictionary with selection statistics
        """
        return {
            'files_scanned': self.files_scanned,
            'files_selected': self.files_selected,
            'directories_scanned': self.directories_scanned,
            'selection_rate': (self.files_selected / max(self.files_scanned, 1)) * 100
        }
    
    def reset_statistics(self):
        """Reset selection statistics."""
        self.files_scanned = 0
        self.files_selected = 0
        self.directories_scanned = 0
    
    def _get_file_info(self, file_path: str, is_directory: bool = False) -> Optional[FileInfo]:
        """
        Get detailed information about a file.
        
        Args:
            file_path: Path to the file
            is_directory: Whether the path is a directory
            
        Returns:
            FileInfo object or None if file is not accessible
        """
        try:
            stat_result = os.stat(file_path)
            path_obj = Path(file_path)
            
            return FileInfo(
                path=os.path.abspath(file_path),
                size=stat_result.st_size,
                modified_time=stat_result.st_mtime,
                created_time=stat_result.st_ctime,
                extension=path_obj.suffix.lower(),
                is_directory=is_directory or os.path.isdir(file_path),
                is_accessible=True
            )
            
        except (OSError, IOError) as e:
            self.logger.warning(f"Cannot access file {file_path}: {e}")
            return FileInfo(
                path=os.path.abspath(file_path),
                size=0,
                modified_time=0,
                created_time=0,
                extension="",
                is_directory=is_directory,
                is_accessible=False,
                error_message=str(e)
            )
        except Exception as e:
            self.logger.error(f"Unexpected error getting file info for {file_path}: {e}")
            return None
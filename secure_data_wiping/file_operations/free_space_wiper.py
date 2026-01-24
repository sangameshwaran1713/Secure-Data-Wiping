#!/usr/bin/env python3
"""
Free Space Wiper Module

Provides free space wiping capabilities to prevent recovery of deleted files
from unallocated disk space.

This module complements file-level wiping by overwriting free space where
deleted file data might still reside.
"""

import os
import tempfile
import random
import shutil
import logging
from typing import Optional, Dict, Any
from pathlib import Path


class FreeSpaceWiperError(Exception):
    """Exception raised by free space wiping operations."""
    pass


class FreeSpaceWiper:
    """
    Free space wiping for enhanced security.
    
    Overwrites free space on file systems to prevent recovery of
    previously deleted files. This is particularly important after
    file-level wiping operations.
    """
    
    def __init__(self):
        """Initialize the free space wiper."""
        self.logger = logging.getLogger(__name__)
        self.bytes_wiped = 0
        self.operations_completed = 0
        
    def wipe_free_space(self, path: str, passes: int = 1, 
                       max_size_mb: Optional[int] = None) -> bool:
        """
        Wipe free space on the file system containing the given path.
        
        Args:
            path: Path on the file system to wipe free space for
            passes: Number of wiping passes
            max_size_mb: Maximum size to wipe in MB (None for all available)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not os.path.exists(path):
                raise FreeSpaceWiperError(f"Path does not exist: {path}")
            
            # Get the directory containing the path
            if os.path.isfile(path):
                target_dir = os.path.dirname(path)
            else:
                target_dir = path
            
            self.logger.info(f"Starting free space wipe for: {target_dir}")
            
            # Get available free space
            free_space = self._get_free_space(target_dir)
            if free_space <= 0:
                self.logger.warning(f"No free space available at {target_dir}")
                return True  # Nothing to wipe
            
            # Determine how much space to wipe
            if max_size_mb:
                max_bytes = max_size_mb * 1024 * 1024
                wipe_size = min(free_space, max_bytes)
            else:
                # Leave some space for system operations (10MB minimum)
                wipe_size = max(0, free_space - (10 * 1024 * 1024))
            
            if wipe_size <= 0:
                self.logger.info("Insufficient free space to perform wiping")
                return True
            
            self.logger.info(f"Wiping {wipe_size / (1024*1024):.1f} MB of free space")
            
            # Perform wiping passes
            for pass_num in range(passes):
                self.logger.info(f"Free space wipe pass {pass_num + 1}/{passes}")
                
                if not self._wipe_free_space_pass(target_dir, wipe_size, pass_num):
                    self.logger.error(f"Free space wipe pass {pass_num + 1} failed")
                    return False
            
            self.bytes_wiped += wipe_size * passes
            self.operations_completed += 1
            
            self.logger.info("Free space wiping completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Free space wiping failed: {e}")
            return False
    
    def _wipe_free_space_pass(self, target_dir: str, wipe_size: int, pass_num: int) -> bool:
        """
        Perform a single pass of free space wiping.
        
        Args:
            target_dir: Directory to create temporary files in
            wipe_size: Number of bytes to wipe
            pass_num: Pass number (affects pattern)
            
        Returns:
            True if successful, False otherwise
        """
        temp_files = []
        
        try:
            # Create multiple temporary files to fill free space
            # This helps with file system fragmentation and ensures better coverage
            chunk_size = min(wipe_size, 100 * 1024 * 1024)  # 100MB chunks max
            remaining_size = wipe_size
            file_counter = 0
            
            while remaining_size > 0:
                current_chunk = min(remaining_size, chunk_size)
                
                # Create temporary file
                temp_file_path = os.path.join(target_dir, f".wipe_temp_{pass_num}_{file_counter}")
                
                try:
                    with open(temp_file_path, 'wb') as temp_file:
                        bytes_written = 0
                        
                        while bytes_written < current_chunk:
                            write_size = min(4096, current_chunk - bytes_written)
                            
                            # Generate pattern based on pass number
                            if pass_num == 0:
                                data = b'\x00' * write_size  # Zeros
                            elif pass_num == 1:
                                data = b'\xFF' * write_size  # Ones
                            else:
                                data = bytes([random.randint(0, 255) for _ in range(write_size)])  # Random
                            
                            temp_file.write(data)
                            bytes_written += write_size
                        
                        # Force write to disk
                        temp_file.flush()
                        os.fsync(temp_file.fileno())
                    
                    temp_files.append(temp_file_path)
                    remaining_size -= current_chunk
                    file_counter += 1
                    
                    # Log progress for large operations
                    if file_counter % 10 == 0:
                        progress = ((wipe_size - remaining_size) / wipe_size) * 100
                        self.logger.debug(f"Free space wipe progress: {progress:.1f}%")
                
                except OSError as e:
                    if "No space left on device" in str(e) or "not enough space" in str(e).lower():
                        # This is expected when we fill up the free space
                        self.logger.debug("Reached end of free space")
                        break
                    else:
                        raise
            
            return True
            
        except Exception as e:
            self.logger.error(f"Free space wipe pass failed: {e}")
            return False
            
        finally:
            # Clean up temporary files
            for temp_file_path in temp_files:
                try:
                    if os.path.exists(temp_file_path):
                        os.remove(temp_file_path)
                        self.logger.debug(f"Removed temporary file: {temp_file_path}")
                except Exception as e:
                    self.logger.warning(f"Could not remove temporary file {temp_file_path}: {e}")
    
    def _get_free_space(self, path: str) -> int:
        """
        Get available free space for the given path.
        
        Args:
            path: Path to check free space for
            
        Returns:
            Free space in bytes
        """
        try:
            if hasattr(shutil, 'disk_usage'):
                # Python 3.3+
                _, _, free = shutil.disk_usage(path)
                return free
            else:
                # Fallback for older Python versions
                import platform
                if platform.system() == 'Windows':
                    import ctypes
                    free_bytes = ctypes.c_ulonglong(0)
                    ctypes.windll.kernel32.GetDiskFreeSpaceExW(
                        ctypes.c_wchar_p(path),
                        ctypes.pointer(free_bytes),
                        None,
                        None
                    )
                    return free_bytes.value
                else:
                    # Unix-like systems
                    statvfs = os.statvfs(path)
                    return statvfs.f_frsize * statvfs.f_bavail
                    
        except Exception as e:
            self.logger.error(f"Could not determine free space for {path}: {e}")
            return 0
    
    def wipe_slack_space(self, file_path: str) -> bool:
        """
        Wipe slack space for a specific file.
        
        Slack space is the unused space in the last cluster/block
        allocated to a file. This space might contain remnants of
        previous file data.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not os.path.exists(file_path):
                self.logger.warning(f"File not found for slack space wiping: {file_path}")
                return False
            
            if not os.path.isfile(file_path):
                self.logger.warning(f"Path is not a file: {file_path}")
                return False
            
            # This is a simplified implementation
            # Real slack space wiping would require:
            # 1. Determining the file system cluster/block size
            # 2. Calculating the actual slack space
            # 3. Directly overwriting the slack space
            
            self.logger.info(f"Slack space wiping requested for: {file_path}")
            self.logger.warning("Slack space wiping is not fully implemented in this version")
            self.logger.warning("For production use, consider specialized tools that can:")
            self.logger.warning("- Access raw disk sectors")
            self.logger.warning("- Calculate exact cluster boundaries")
            self.logger.warning("- Overwrite slack space directly")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Slack space wiping failed for {file_path}: {e}")
            return False
    
    def estimate_wipe_time(self, path: str, passes: int = 1) -> Optional[float]:
        """
        Estimate time required for free space wiping.
        
        Args:
            path: Path to estimate for
            passes: Number of passes
            
        Returns:
            Estimated time in seconds, or None if cannot estimate
        """
        try:
            free_space = self._get_free_space(path)
            if free_space <= 0:
                return 0.0
            
            # Rough estimate: 50 MB/s write speed (conservative)
            write_speed_mb_per_sec = 50
            write_speed_bytes_per_sec = write_speed_mb_per_sec * 1024 * 1024
            
            # Leave some space for system operations
            wipe_size = max(0, free_space - (10 * 1024 * 1024))
            
            estimated_seconds = (wipe_size * passes) / write_speed_bytes_per_sec
            
            return estimated_seconds
            
        except Exception as e:
            self.logger.error(f"Could not estimate wipe time for {path}: {e}")
            return None
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get free space wiping statistics.
        
        Returns:
            Dictionary with wiping statistics
        """
        return {
            'operations_completed': self.operations_completed,
            'bytes_wiped': self.bytes_wiped,
            'mb_wiped': self.bytes_wiped / (1024 * 1024),
            'gb_wiped': self.bytes_wiped / (1024 * 1024 * 1024)
        }
    
    def reset_statistics(self):
        """Reset wiping statistics."""
        self.bytes_wiped = 0
        self.operations_completed = 0
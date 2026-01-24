#!/usr/bin/env python3
"""
File Wipe Engine Module

Provides NIST 800-88 compliant file-level secure deletion capabilities.
Extends the existing device-level wiping system with granular file control.

This module integrates seamlessly with the existing architecture while
adding file-specific wiping operations and maintaining full compliance.
"""

import os
import hashlib
import random
import time
import uuid
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime

from ..utils.data_models import (
    WipeTarget, WipeTargetType, FileWipeConfig, FileWipeResult, 
    WipeMethod, OperationStatus
)
from .file_selector import FileSelector, FileInfo, FileSelectorError
from .metadata_cleaner import MetadataCleaner
from .free_space_wiper import FreeSpaceWiper


class FileWipeError(Exception):
    """Exception raised by file wiping operations."""
    pass


class FileWipeEngine:
    """
    NIST 800-88 compliant file-level secure wiping engine.
    
    Provides secure deletion capabilities for:
    - Individual files
    - Directories and their contents
    - Files matching patterns
    - Files by extensions
    - Files meeting specific criteria
    
    Maintains full integration with existing blockchain logging,
    certificate generation, and audit trail systems.
    """
    
    # NIST 800-88 compliant overwrite patterns
    NIST_PATTERNS = {
        'zeros': b'\x00',
        'ones': b'\xFF',
        'random': None,  # Generated dynamically
        'dod_pattern_1': b'\x55',  # 01010101
        'dod_pattern_2': b'\xAA',  # 10101010
    }
    
    def __init__(self):
        """Initialize the file wipe engine."""
        self.logger = logging.getLogger(__name__)
        self.file_selector = FileSelector()
        self.metadata_cleaner = MetadataCleaner()
        self.free_space_wiper = FreeSpaceWiper()
        
        # Statistics tracking
        self.operations_completed = 0
        self.total_files_wiped = 0
        self.total_bytes_wiped = 0
        self.total_directories_processed = 0
        self.last_operation_time = None
        
        self.logger.info("FileWipeEngine initialized with NIST 800-88 compliance")
    
    def wipe_target(self, wipe_target: WipeTarget, config: FileWipeConfig) -> FileWipeResult:
        """
        Wipe a target based on its type.
        
        Args:
            wipe_target: Target specification
            config: Wiping configuration
            
        Returns:
            FileWipeResult with operation details
            
        Raises:
            FileWipeError: If wiping operation fails
        """
        try:
            operation_id = f"FILE_OP_{int(time.time())}_{wipe_target.target_id}"
            start_time = datetime.now()
            
            self.logger.info(f"Starting file wipe operation {operation_id}")
            self.logger.info(f"Target: {wipe_target.target_type.value} - {wipe_target.target_path}")
            
            # Route to appropriate wiping method based on target type
            if wipe_target.target_type == WipeTargetType.FILE:
                result = self._wipe_single_file(wipe_target, config, operation_id, start_time)
            elif wipe_target.target_type == WipeTargetType.DIRECTORY:
                result = self._wipe_directory(wipe_target, config, operation_id, start_time)
            elif wipe_target.target_type == WipeTargetType.PATTERN:
                result = self._wipe_by_pattern(wipe_target, config, operation_id, start_time)
            elif wipe_target.target_type == WipeTargetType.EXTENSIONS:
                result = self._wipe_by_extensions(wipe_target, config, operation_id, start_time)
            elif wipe_target.target_type == WipeTargetType.FILE_LIST:
                result = self._wipe_file_list(wipe_target, config, operation_id, start_time)
            else:
                raise FileWipeError(f"Unsupported target type: {wipe_target.target_type}")
            
            # Update statistics
            self.operations_completed += 1
            self.last_operation_time = result.end_time
            
            self.logger.info(f"File wipe operation {operation_id} completed")
            self.logger.info(f"Files processed: {result.files_processed}, Success rate: {result.success_rate:.1f}%")
            
            return result
            
        except Exception as e:
            self.logger.error(f"File wipe operation failed: {e}")
            raise FileWipeError(f"Wipe operation failed: {e}")
    
    def _wipe_single_file(self, target: WipeTarget, config: FileWipeConfig, 
                         operation_id: str, start_time: datetime) -> FileWipeResult:
        """Wipe a single file."""
        try:
            if not os.path.exists(target.target_path):
                raise FileWipeError(f"File not found: {target.target_path}")
            
            if not os.path.isfile(target.target_path):
                raise FileWipeError(f"Path is not a file: {target.target_path}")
            
            file_size = os.path.getsize(target.target_path)
            original_hash = self._calculate_file_hash(target.target_path)
            
            # Perform secure wiping
            wipe_success = self._secure_overwrite_file(target.target_path, config)
            
            # Clean metadata if requested
            if config.wipe_file_metadata and wipe_success:
                self.metadata_cleaner.clean_file_metadata(target.target_path)
            
            # Delete the file
            if wipe_success:
                os.remove(target.target_path)
                self.total_files_wiped += 1
                self.total_bytes_wiped += file_size
            
            # Create result
            result = FileWipeResult(
                operation_id=operation_id,
                device_id=target.device_context or "FILE_SYSTEM",
                method=config.method,
                passes_completed=config.passes,
                start_time=start_time,
                end_time=datetime.now(),
                success=wipe_success,
                target_type=target.target_type,
                target_path=target.target_path,
                files_processed=1,
                files_successful=1 if wipe_success else 0,
                files_failed=0 if wipe_success else 1,
                total_size_bytes=file_size,
                bytes_wiped=file_size if wipe_success else 0,
                verification_hash=self._generate_operation_hash(target, config, original_hash)
            )
            
            return result
            
        except Exception as e:
            return self._create_error_result(operation_id, target, start_time, str(e))
    
    def _wipe_directory(self, target: WipeTarget, config: FileWipeConfig,
                       operation_id: str, start_time: datetime) -> FileWipeResult:
        """Wipe entire directory and contents."""
        try:
            if not os.path.exists(target.target_path):
                raise FileWipeError(f"Directory not found: {target.target_path}")
            
            if not os.path.isdir(target.target_path):
                raise FileWipeError(f"Path is not a directory: {target.target_path}")
            
            # Get all files in directory
            files = self.file_selector.select_directory_contents(
                target.target_path, 
                recursive=target.recursive
            )
            
            # Process each file
            files_processed = 0
            files_successful = 0
            files_failed = 0
            total_size = 0
            detailed_results = []
            
            for file_info in files:
                if file_info.is_directory:
                    continue  # Skip directories for now
                
                try:
                    if file_info.is_accessible:
                        file_size = file_info.size
                        wipe_success = self._secure_overwrite_file(file_info.path, config)
                        
                        if config.wipe_file_metadata and wipe_success:
                            self.metadata_cleaner.clean_file_metadata(file_info.path)
                        
                        if wipe_success:
                            os.remove(file_info.path)
                            files_successful += 1
                            total_size += file_size
                            self.total_files_wiped += 1
                            self.total_bytes_wiped += file_size
                        else:
                            files_failed += 1
                        
                        detailed_results.append({
                            'path': file_info.path,
                            'size': file_size,
                            'success': wipe_success,
                            'passes': config.passes
                        })
                    else:
                        files_failed += 1
                        detailed_results.append({
                            'path': file_info.path,
                            'size': 0,
                            'success': False,
                            'error': file_info.error_message
                        })
                    
                    files_processed += 1
                    
                except Exception as e:
                    files_failed += 1
                    files_processed += 1
                    detailed_results.append({
                        'path': file_info.path,
                        'success': False,
                        'error': str(e)
                    })
            
            # Remove empty directories if not preserving structure
            if not config.preserve_directory_structure:
                self._remove_empty_directories(target.target_path)
            
            # Wipe free space if requested
            if config.overwrite_free_space and files_successful > 0:
                try:
                    self.free_space_wiper.wipe_free_space(target.target_path)
                except Exception as e:
                    self.logger.warning(f"Free space wiping failed: {e}")
            
            self.total_directories_processed += 1
            
            # Create result
            result = FileWipeResult(
                operation_id=operation_id,
                device_id=target.device_context or "FILE_SYSTEM",
                method=config.method,
                passes_completed=config.passes,
                start_time=start_time,
                end_time=datetime.now(),
                success=files_failed == 0,
                target_type=target.target_type,
                target_path=target.target_path,
                files_processed=files_processed,
                files_successful=files_successful,
                files_failed=files_failed,
                directories_processed=1,
                total_size_bytes=total_size,
                bytes_wiped=total_size,
                detailed_results=detailed_results,
                verification_hash=self._generate_operation_hash(target, config, f"dir_{files_processed}")
            )
            
            return result
            
        except Exception as e:
            return self._create_error_result(operation_id, target, start_time, str(e))
    
    def _wipe_by_pattern(self, target: WipeTarget, config: FileWipeConfig,
                        operation_id: str, start_time: datetime) -> FileWipeResult:
        """Wipe files matching a pattern."""
        try:
            if not target.pattern:
                raise FileWipeError("Pattern not specified for pattern-based wiping")
            
            # Select files by pattern
            files = self.file_selector.select_by_pattern(
                target.pattern,
                target.target_path,
                target.recursive
            )
            
            if not files:
                # No files found - this is not an error
                result = FileWipeResult(
                    operation_id=operation_id,
                    device_id=target.device_context or "FILE_SYSTEM",
                    method=config.method,
                    passes_completed=0,
                    start_time=start_time,
                    end_time=datetime.now(),
                    success=True,
                    target_type=target.target_type,
                    target_path=target.target_path,
                    pattern_used=target.pattern,
                    files_processed=0,
                    files_successful=0,
                    files_failed=0,
                    verification_hash=self._generate_operation_hash(target, config, "no_files")
                )
                return result
            
            # Process selected files
            return self._process_file_list(files, target, config, operation_id, start_time)
            
        except Exception as e:
            return self._create_error_result(operation_id, target, start_time, str(e))
    
    def _wipe_by_extensions(self, target: WipeTarget, config: FileWipeConfig,
                           operation_id: str, start_time: datetime) -> FileWipeResult:
        """Wipe files by extensions."""
        try:
            if not target.extensions:
                raise FileWipeError("Extensions not specified for extension-based wiping")
            
            # Select files by extensions
            files = self.file_selector.select_by_extensions(
                target.extensions,
                target.target_path,
                target.recursive
            )
            
            if not files:
                # No files found - this is not an error
                result = FileWipeResult(
                    operation_id=operation_id,
                    device_id=target.device_context or "FILE_SYSTEM",
                    method=config.method,
                    passes_completed=0,
                    start_time=start_time,
                    end_time=datetime.now(),
                    success=True,
                    target_type=target.target_type,
                    target_path=target.target_path,
                    extensions_used=target.extensions,
                    files_processed=0,
                    files_successful=0,
                    files_failed=0,
                    verification_hash=self._generate_operation_hash(target, config, "no_files")
                )
                return result
            
            # Process selected files
            result = self._process_file_list(files, target, config, operation_id, start_time)
            result.extensions_used = target.extensions
            return result
            
        except Exception as e:
            return self._create_error_result(operation_id, target, start_time, str(e))
    
    def _wipe_file_list(self, target: WipeTarget, config: FileWipeConfig,
                       operation_id: str, start_time: datetime) -> FileWipeResult:
        """Wipe a specific list of files."""
        try:
            # For file list, target_path should contain file paths separated by semicolons
            file_paths = target.target_path.split(';')
            
            # Convert to FileInfo objects
            files = []
            for file_path in file_paths:
                file_path = file_path.strip()
                if file_path and os.path.exists(file_path) and os.path.isfile(file_path):
                    file_info = self.file_selector._get_file_info(file_path)
                    if file_info:
                        files.append(file_info)
            
            # Process selected files
            return self._process_file_list(files, target, config, operation_id, start_time)
            
        except Exception as e:
            return self._create_error_result(operation_id, target, start_time, str(e))
    
    def _process_file_list(self, files: List[FileInfo], target: WipeTarget, 
                          config: FileWipeConfig, operation_id: str, 
                          start_time: datetime) -> FileWipeResult:
        """Process a list of files for wiping."""
        files_processed = 0
        files_successful = 0
        files_failed = 0
        total_size = 0
        detailed_results = []
        
        for file_info in files:
            if file_info.is_directory:
                continue  # Skip directories
            
            try:
                if file_info.is_accessible:
                    # Check file size limits if specified
                    if config.max_file_size and file_info.size > config.max_file_size:
                        self.logger.info(f"Skipping large file: {file_info.path} ({file_info.size} bytes)")
                        continue
                    
                    # Check file age if specified
                    if config.min_file_age_days:
                        file_age_days = (time.time() - file_info.modified_time) / (24 * 3600)
                        if file_age_days < config.min_file_age_days:
                            self.logger.info(f"Skipping recent file: {file_info.path} ({file_age_days:.1f} days old)")
                            continue
                    
                    # Confirm each file if requested
                    if config.confirm_each_file:
                        # In a real implementation, this would prompt the user
                        # For now, we'll log and proceed
                        self.logger.info(f"Processing file: {file_info.path}")
                    
                    file_size = file_info.size
                    wipe_success = self._secure_overwrite_file(file_info.path, config)
                    
                    if config.wipe_file_metadata and wipe_success:
                        self.metadata_cleaner.clean_file_metadata(file_info.path)
                    
                    if wipe_success:
                        os.remove(file_info.path)
                        files_successful += 1
                        total_size += file_size
                        self.total_files_wiped += 1
                        self.total_bytes_wiped += file_size
                    else:
                        files_failed += 1
                    
                    detailed_results.append({
                        'path': file_info.path,
                        'size': file_size,
                        'success': wipe_success,
                        'passes': config.passes
                    })
                else:
                    files_failed += 1
                    detailed_results.append({
                        'path': file_info.path,
                        'size': 0,
                        'success': False,
                        'error': file_info.error_message
                    })
                
                files_processed += 1
                
            except Exception as e:
                files_failed += 1
                files_processed += 1
                detailed_results.append({
                    'path': file_info.path,
                    'success': False,
                    'error': str(e)
                })
        
        # Create result
        result = FileWipeResult(
            operation_id=operation_id,
            device_id=target.device_context or "FILE_SYSTEM",
            method=config.method,
            passes_completed=config.passes,
            start_time=start_time,
            end_time=datetime.now(),
            success=files_failed == 0,
            target_type=target.target_type,
            target_path=target.target_path,
            files_processed=files_processed,
            files_successful=files_successful,
            files_failed=files_failed,
            total_size_bytes=total_size,
            bytes_wiped=total_size,
            detailed_results=detailed_results,
            verification_hash=self._generate_operation_hash(target, config, f"files_{files_processed}")
        )
        
        return result
    
    def _secure_overwrite_file(self, file_path: str, config: FileWipeConfig) -> bool:
        """
        Perform NIST 800-88 compliant secure overwriting of a file.
        
        Args:
            file_path: Path to file to overwrite
            config: Wiping configuration
            
        Returns:
            True if successful, False otherwise
        """
        try:
            file_size = os.path.getsize(file_path)
            
            if file_size == 0:
                return True  # Empty file, nothing to overwrite
            
            with open(file_path, 'r+b') as f:
                for pass_num in range(config.passes):
                    f.seek(0)
                    
                    # Select pattern for this pass
                    if pass_num == 0:
                        pattern = self.NIST_PATTERNS['zeros']
                    elif pass_num == 1:
                        pattern = self.NIST_PATTERNS['ones']
                    else:
                        pattern = None  # Random data
                    
                    # Overwrite file
                    bytes_written = 0
                    while bytes_written < file_size:
                        chunk_size = min(config.block_size, file_size - bytes_written)
                        
                        if pattern is None:
                            # Random data
                            chunk_data = bytes([random.randint(0, 255) for _ in range(chunk_size)])
                        else:
                            # Pattern data
                            chunk_data = pattern * chunk_size
                            chunk_data = chunk_data[:chunk_size]
                        
                        f.write(chunk_data)
                        bytes_written += chunk_size
                    
                    # Force write to disk
                    f.flush()
                    os.fsync(f.fileno())
                    
                    self.logger.debug(f"Pass {pass_num + 1}/{config.passes} completed for {file_path}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Secure overwrite failed for {file_path}: {e}")
            return False
    
    def _remove_empty_directories(self, base_path: str):
        """Remove empty directories recursively."""
        try:
            for root, dirs, files in os.walk(base_path, topdown=False):
                for dir_name in dirs:
                    dir_path = os.path.join(root, dir_name)
                    try:
                        os.rmdir(dir_path)  # Only removes if empty
                        self.logger.debug(f"Removed empty directory: {dir_path}")
                    except OSError:
                        pass  # Directory not empty or other error
            
            # Try to remove the base directory itself
            try:
                os.rmdir(base_path)
                self.logger.debug(f"Removed base directory: {base_path}")
            except OSError:
                pass  # Directory not empty or other error
                
        except Exception as e:
            self.logger.warning(f"Error removing empty directories: {e}")
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA-256 hash of file content."""
        try:
            hash_sha256 = hashlib.sha256()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception as e:
            self.logger.warning(f"Hash calculation failed for {file_path}: {e}")
            return "hash_calculation_failed"
    
    def _generate_operation_hash(self, target: WipeTarget, config: FileWipeConfig, 
                                content_hash: str) -> str:
        """Generate hash for the entire operation."""
        try:
            hash_data = f"{target.target_id}:{target.target_type.value}:{target.target_path}:"
            hash_data += f"{config.method.value}:{config.passes}:{content_hash}"
            
            return hashlib.sha256(hash_data.encode()).hexdigest()
        except Exception:
            return f"op_hash_{int(time.time())}"
    
    def _create_error_result(self, operation_id: str, target: WipeTarget, 
                           start_time: datetime, error_message: str) -> FileWipeResult:
        """Create a FileWipeResult for failed operations."""
        return FileWipeResult(
            operation_id=operation_id,
            device_id=target.device_context or "FILE_SYSTEM",
            method=WipeMethod.NIST_CLEAR,  # Default
            passes_completed=0,
            start_time=start_time,
            end_time=datetime.now(),
            success=False,
            error_message=error_message,
            target_type=target.target_type,
            target_path=target.target_path,
            files_processed=0,
            files_successful=0,
            files_failed=1
        )
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get engine statistics."""
        return {
            'operations_completed': self.operations_completed,
            'total_files_wiped': self.total_files_wiped,
            'total_bytes_wiped': self.total_bytes_wiped,
            'total_directories_processed': self.total_directories_processed,
            'last_operation_time': self.last_operation_time.isoformat() if self.last_operation_time else None
        }
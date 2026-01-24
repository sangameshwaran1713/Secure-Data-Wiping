"""
File Operations Module

This module provides file-level secure deletion capabilities that extend
the existing device-level wiping system. It maintains full compatibility
with the current architecture while adding granular file control.

Key Components:
- FileSelector: Pattern-based file selection and filtering
- FileWipeEngine: NIST-compliant file-level wiping operations
- MetadataCleaner: File system metadata wiping
- FreeSpaceWiper: Free space overwriting capabilities

Integration:
- Extends existing WipeEngine with file-level operations
- Uses same blockchain logging and certificate generation
- Maintains NIST 800-88 compliance for all operations
- Provides seamless CLI integration
"""

from .file_selector import FileSelector, FileSelectorError
from .file_wipe_engine import FileWipeEngine, FileWipeError
from .metadata_cleaner import MetadataCleaner
from .free_space_wiper import FreeSpaceWiper

__all__ = [
    'FileSelector',
    'FileSelectorError', 
    'FileWipeEngine',
    'FileWipeError',
    'MetadataCleaner',
    'FreeSpaceWiper'
]
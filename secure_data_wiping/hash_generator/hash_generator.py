"""
Hash Generator Implementation

Provides SHA-256 cryptographic hash generation for wiping operation verification.
Implements deterministic hash generation and tamper detection capabilities.
"""

import hashlib
import json
from datetime import datetime
from typing import Dict, Any, Optional
from ..utils.data_models import HashData, WipeResult


class HashGenerator:
    """
    Generates and verifies SHA-256 cryptographic hashes for wiping operations.
    
    This class provides deterministic hash generation from wiping operation metadata,
    ensuring consistent hashes for identical operations and enabling tamper detection.
    """
    
    def __init__(self, algorithm: str = "sha256"):
        """
        Initialize the hash generator.
        
        Args:
            algorithm: Hashing algorithm to use (default: sha256)
            
        Raises:
            ValueError: If unsupported algorithm is specified
        """
        if algorithm.lower() != "sha256":
            raise ValueError(f"Unsupported algorithm: {algorithm}. Only SHA-256 is supported.")
        
        self.algorithm = algorithm.lower()
    
    def generate_wipe_hash(self, wipe_result: WipeResult) -> str:
        """
        Generate SHA-256 hash from wiping operation result.
        
        Creates a deterministic hash from the wiping operation metadata,
        ensuring identical operations produce identical hashes.
        
        Args:
            wipe_result: Completed wiping operation result
            
        Returns:
            str: Hexadecimal SHA-256 hash of the operation
            
        Raises:
            ValueError: If required fields are missing or invalid
        """
        if not wipe_result:
            raise ValueError("WipeResult cannot be None")
        
        if not wipe_result.device_id:
            raise ValueError("Device ID is required for hash generation")
        
        if not wipe_result.start_time:
            raise ValueError("Start time is required for hash generation")
        
        if not wipe_result.success:
            raise ValueError("Cannot generate hash for failed wiping operation")
        
        # Create HashData from WipeResult
        hash_data = HashData(
            device_id=wipe_result.device_id,
            timestamp=wipe_result.start_time.isoformat(),
            method=wipe_result.method.value if hasattr(wipe_result.method, 'value') else str(wipe_result.method),
            passes=wipe_result.passes_completed,
            operator=wipe_result.operator_id,
            verification_data=wipe_result.verification_hash
        )
        
        return self._generate_hash_from_data(hash_data)
    
    def generate_hash_from_metadata(self, hash_data: HashData) -> str:
        """
        Generate SHA-256 hash from HashData metadata.
        
        Args:
            hash_data: Structured metadata for hash generation
            
        Returns:
            str: Hexadecimal SHA-256 hash
            
        Raises:
            ValueError: If required fields are missing
        """
        if not hash_data:
            raise ValueError("HashData cannot be None")
        
        return self._generate_hash_from_data(hash_data)
    
    def _generate_hash_from_data(self, hash_data: HashData) -> str:
        """
        Internal method to generate hash from HashData.
        
        Implements deterministic hash generation with consistent field ordering.
        
        Args:
            hash_data: Structured metadata for hash generation
            
        Returns:
            str: Hexadecimal SHA-256 hash
            
        Raises:
            ValueError: If required fields are missing
        """
        # Validate required fields
        required_fields = ['device_id', 'timestamp', 'method', 'passes', 'operator']
        for field in required_fields:
            if not getattr(hash_data, field, None):
                raise ValueError(f"Required field '{field}' is missing or empty")
        
        # Create ordered dictionary for deterministic hashing
        # Order is critical for hash consistency
        ordered_data = {
            'device_id': str(hash_data.device_id),
            'timestamp': str(hash_data.timestamp),
            'method': str(hash_data.method),
            'passes': int(hash_data.passes),
            'operator': str(hash_data.operator)
        }
        
        # Add optional fields if present
        if hash_data.verification_data:
            ordered_data['verification_data'] = str(hash_data.verification_data)
        
        if hash_data.device_info:
            # Sort device info keys for consistency
            device_info_sorted = {k: v for k, v in sorted(hash_data.device_info.items()) if v is not None}
            if device_info_sorted:
                ordered_data['device_info'] = device_info_sorted
        
        # Convert to JSON with sorted keys for deterministic output
        json_data = json.dumps(ordered_data, sort_keys=True, separators=(',', ':'))
        
        # Generate SHA-256 hash
        hash_object = hashlib.sha256(json_data.encode('utf-8'))
        return hash_object.hexdigest()
    
    def verify_hash(self, wipe_result: WipeResult, expected_hash: str) -> bool:
        """
        Verify hash against wiping operation result for tamper detection.
        
        Regenerates hash from operation data and compares with expected hash
        to detect any tampering or data corruption.
        
        Args:
            wipe_result: Wiping operation result to verify
            expected_hash: Expected hash value for comparison
            
        Returns:
            bool: True if hash matches (no tampering), False otherwise
            
        Raises:
            ValueError: If inputs are invalid
        """
        if not expected_hash:
            raise ValueError("Expected hash cannot be empty")
        
        if not isinstance(expected_hash, str):
            raise ValueError("Expected hash must be a string")
        
        # Remove any whitespace and convert to lowercase for comparison
        expected_hash = expected_hash.strip().lower()
        
        # Validate hash format (64 hex characters for SHA-256)
        if len(expected_hash) != 64:
            raise ValueError("Invalid hash length. SHA-256 hash must be 64 characters")
        
        if not all(c in '0123456789abcdef' for c in expected_hash):
            raise ValueError("Invalid hash format. Hash must contain only hexadecimal characters")
        
        try:
            # Generate hash from current data
            current_hash = self.generate_wipe_hash(wipe_result)
            
            # Compare hashes (case-insensitive)
            return current_hash.lower() == expected_hash
            
        except Exception as e:
            # If hash generation fails, consider it a verification failure
            return False
    
    def verify_hash_from_metadata(self, hash_data: HashData, expected_hash: str) -> bool:
        """
        Verify hash against HashData metadata for tamper detection.
        
        Args:
            hash_data: Metadata to verify
            expected_hash: Expected hash value for comparison
            
        Returns:
            bool: True if hash matches (no tampering), False otherwise
        """
        if not expected_hash:
            raise ValueError("Expected hash cannot be empty")
        
        expected_hash = expected_hash.strip().lower()
        
        try:
            current_hash = self.generate_hash_from_metadata(hash_data)
            return current_hash.lower() == expected_hash
        except Exception:
            return False
    
    def create_hash_data_from_operation(self, wipe_result: WipeResult, 
                                      device_info: Optional[Dict[str, Any]] = None) -> HashData:
        """
        Create HashData structure from WipeResult for hash generation.
        
        Args:
            wipe_result: Wiping operation result
            device_info: Optional additional device information
            
        Returns:
            HashData: Structured data for hash generation
            
        Raises:
            ValueError: If required fields are missing
        """
        if not wipe_result:
            raise ValueError("WipeResult cannot be None")
        
        return HashData(
            device_id=wipe_result.device_id,
            timestamp=wipe_result.start_time.isoformat() if wipe_result.start_time else datetime.now().isoformat(),
            method=wipe_result.method.value if hasattr(wipe_result.method, 'value') else str(wipe_result.method),
            passes=wipe_result.passes_completed,
            operator=wipe_result.operator_id,
            verification_data=wipe_result.verification_hash,
            device_info=device_info
        )
    
    def get_algorithm(self) -> str:
        """
        Get the current hashing algorithm.
        
        Returns:
            str: Current algorithm name
        """
        return self.algorithm
    
    def get_hash_info(self, hash_value: str) -> Dict[str, Any]:
        """
        Get information about a hash value.
        
        Args:
            hash_value: Hash to analyze
            
        Returns:
            Dict containing hash information
        """
        if not hash_value:
            return {'valid': False, 'error': 'Hash value is empty'}
        
        hash_value = hash_value.strip()
        
        info = {
            'algorithm': self.algorithm,
            'length': len(hash_value),
            'valid': False,
            'format': 'hexadecimal' if all(c in '0123456789abcdefABCDEF' for c in hash_value) else 'invalid'
        }
        
        # Check if it's a valid SHA-256 hash
        if len(hash_value) == 64 and info['format'] == 'hexadecimal':
            info['valid'] = True
        else:
            info['error'] = f"Invalid SHA-256 hash. Expected 64 hex characters, got {len(hash_value)}"
        
        return info
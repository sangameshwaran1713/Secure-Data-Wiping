"""
Unit tests for Hash Generator component.

Tests specific examples, edge cases, and error handling scenarios.
"""

import pytest
from datetime import datetime
from secure_data_wiping.hash_generator import HashGenerator
from secure_data_wiping.utils.data_models import HashData, WipeResult, WipeMethod


class TestHashGeneratorUnit:
    """Unit tests for HashGenerator class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.hash_gen = HashGenerator()
    
    def test_hash_generator_initialization(self):
        """Test HashGenerator initialization."""
        # Default initialization
        hash_gen = HashGenerator()
        assert hash_gen.get_algorithm() == "sha256"
        
        # Explicit SHA-256 initialization
        hash_gen_explicit = HashGenerator("sha256")
        assert hash_gen_explicit.get_algorithm() == "sha256"
        
        # Case insensitive
        hash_gen_upper = HashGenerator("SHA256")
        assert hash_gen_upper.get_algorithm() == "sha256"
    
    def test_unsupported_algorithm_rejection(self):
        """Test that unsupported algorithms are rejected."""
        unsupported_algorithms = ["md5", "sha1", "sha512", "blake2b", "invalid"]
        
        for algorithm in unsupported_algorithms:
            with pytest.raises(ValueError, match="Unsupported algorithm"):
                HashGenerator(algorithm)
    
    def test_generate_hash_from_metadata_missing_fields(self):
        """Test hash generation with missing required fields."""
        # Missing device_id
        with pytest.raises(ValueError, match="Required field 'device_id'"):
            hash_data = HashData(
                device_id="",
                timestamp="2026-01-08T10:00:00",
                method="clear",
                passes=3,
                operator="test_op"
            )
            self.hash_gen.generate_hash_from_metadata(hash_data)
        
        # Missing timestamp
        with pytest.raises(ValueError, match="Required field 'timestamp'"):
            hash_data = HashData(
                device_id="device_001",
                timestamp="",
                method="clear",
                passes=3,
                operator="test_op"
            )
            self.hash_gen.generate_hash_from_metadata(hash_data)
        
        # Missing method
        with pytest.raises(ValueError, match="Required field 'method'"):
            hash_data = HashData(
                device_id="device_001",
                timestamp="2026-01-08T10:00:00",
                method="",
                passes=3,
                operator="test_op"
            )
            self.hash_gen.generate_hash_from_metadata(hash_data)
        
        # Missing operator
        with pytest.raises(ValueError, match="Required field 'operator'"):
            hash_data = HashData(
                device_id="device_001",
                timestamp="2026-01-08T10:00:00",
                method="clear",
                passes=3,
                operator=""
            )
            self.hash_gen.generate_hash_from_metadata(hash_data)
        
        # None input
        with pytest.raises(ValueError, match="HashData cannot be None"):
            self.hash_gen.generate_hash_from_metadata(None)
    
    def test_generate_wipe_hash_invalid_inputs(self):
        """Test wipe hash generation with invalid inputs."""
        # None input
        with pytest.raises(ValueError, match="WipeResult cannot be None"):
            self.hash_gen.generate_wipe_hash(None)
        
        # Missing device_id
        wipe_result = WipeResult(
            operation_id="op_001",
            device_id="",
            method=WipeMethod.NIST_CLEAR,
            passes_completed=3,
            start_time=datetime.now(),
            success=True,
            operator_id="test_op"
        )
        
        with pytest.raises(ValueError, match="Device ID is required"):
            self.hash_gen.generate_wipe_hash(wipe_result)
        
        # Missing start_time
        wipe_result = WipeResult(
            operation_id="op_001",
            device_id="device_001",
            method=WipeMethod.NIST_CLEAR,
            passes_completed=3,
            start_time=None,
            success=True,
            operator_id="test_op"
        )
        
        with pytest.raises(ValueError, match="Start time is required"):
            self.hash_gen.generate_wipe_hash(wipe_result)
        
        # Failed operation
        wipe_result = WipeResult(
            operation_id="op_001",
            device_id="device_001",
            method=WipeMethod.NIST_CLEAR,
            passes_completed=3,
            start_time=datetime.now(),
            success=False,  # Failed operation
            operator_id="test_op"
        )
        
        with pytest.raises(ValueError, match="Cannot generate hash for failed wiping operation"):
            self.hash_gen.generate_wipe_hash(wipe_result)
    
    def test_verify_hash_invalid_inputs(self):
        """Test hash verification with invalid inputs."""
        valid_wipe_result = WipeResult(
            operation_id="op_001",
            device_id="device_001",
            method=WipeMethod.NIST_CLEAR,
            passes_completed=3,
            start_time=datetime.now(),
            success=True,
            operator_id="test_op"
        )
        
        # Empty hash
        with pytest.raises(ValueError, match="Expected hash cannot be empty"):
            self.hash_gen.verify_hash(valid_wipe_result, "")
        
        # None hash
        with pytest.raises(ValueError, match="Expected hash cannot be empty"):
            self.hash_gen.verify_hash(valid_wipe_result, None)
        
        # Non-string hash
        with pytest.raises(ValueError, match="Expected hash must be a string"):
            self.hash_gen.verify_hash(valid_wipe_result, 12345)
        
        # Invalid hash length
        with pytest.raises(ValueError, match="Invalid hash length"):
            self.hash_gen.verify_hash(valid_wipe_result, "a" * 63)  # Too short
        
        with pytest.raises(ValueError, match="Invalid hash length"):
            self.hash_gen.verify_hash(valid_wipe_result, "a" * 65)  # Too long
        
        # Invalid hex characters
        with pytest.raises(ValueError, match="Invalid hash format"):
            self.hash_gen.verify_hash(valid_wipe_result, "g" * 64)  # Invalid hex
    
    def test_verify_hash_from_metadata_invalid_inputs(self):
        """Test metadata hash verification with invalid inputs."""
        valid_hash_data = HashData(
            device_id="device_001",
            timestamp="2026-01-08T10:00:00",
            method="clear",
            passes=3,
            operator="test_op"
        )
        
        # Empty hash
        with pytest.raises(ValueError, match="Expected hash cannot be empty"):
            self.hash_gen.verify_hash_from_metadata(valid_hash_data, "")
        
        # None hash
        with pytest.raises(ValueError, match="Expected hash cannot be empty"):
            self.hash_gen.verify_hash_from_metadata(valid_hash_data, None)
    
    def test_hash_generation_with_optional_fields(self):
        """Test hash generation with optional fields."""
        # Base data without optional fields
        base_data = HashData(
            device_id="device_001",
            timestamp="2026-01-08T10:00:00",
            method="clear",
            passes=3,
            operator="test_op"
        )
        
        base_hash = self.hash_gen.generate_hash_from_metadata(base_data)
        
        # Data with verification_data
        data_with_verification = HashData(
            device_id="device_001",
            timestamp="2026-01-08T10:00:00",
            method="clear",
            passes=3,
            operator="test_op",
            verification_data="verification_hash_123"
        )
        
        verification_hash = self.hash_gen.generate_hash_from_metadata(data_with_verification)
        assert base_hash != verification_hash, "Hash should change when verification_data is added"
        
        # Data with device_info
        data_with_device_info = HashData(
            device_id="device_001",
            timestamp="2026-01-08T10:00:00",
            method="clear",
            passes=3,
            operator="test_op",
            device_info={
                "manufacturer": "Test Corp",
                "model": "Test Model",
                "serial": "SN123456"
            }
        )
        
        device_info_hash = self.hash_gen.generate_hash_from_metadata(data_with_device_info)
        assert base_hash != device_info_hash, "Hash should change when device_info is added"
        assert verification_hash != device_info_hash, "Different optional fields should produce different hashes"
    
    def test_device_info_ordering_consistency(self):
        """Test that device_info dictionary ordering doesn't affect hash."""
        # Same device info in different orders
        data1 = HashData(
            device_id="device_001",
            timestamp="2026-01-08T10:00:00",
            method="clear",
            passes=3,
            operator="test_op",
            device_info={
                "manufacturer": "Test Corp",
                "model": "Test Model",
                "serial": "SN123456"
            }
        )
        
        data2 = HashData(
            device_id="device_001",
            timestamp="2026-01-08T10:00:00",
            method="clear",
            passes=3,
            operator="test_op",
            device_info={
                "serial": "SN123456",
                "manufacturer": "Test Corp",
                "model": "Test Model"
            }
        )
        
        hash1 = self.hash_gen.generate_hash_from_metadata(data1)
        hash2 = self.hash_gen.generate_hash_from_metadata(data2)
        
        assert hash1 == hash2, "Hash should be consistent regardless of device_info key ordering"
    
    def test_device_info_none_values_filtering(self):
        """Test that None values in device_info are filtered out."""
        data_with_none = HashData(
            device_id="device_001",
            timestamp="2026-01-08T10:00:00",
            method="clear",
            passes=3,
            operator="test_op",
            device_info={
                "manufacturer": "Test Corp",
                "model": None,  # None value should be filtered
                "serial": "SN123456",
                "capacity": None  # None value should be filtered
            }
        )
        
        data_without_none = HashData(
            device_id="device_001",
            timestamp="2026-01-08T10:00:00",
            method="clear",
            passes=3,
            operator="test_op",
            device_info={
                "manufacturer": "Test Corp",
                "serial": "SN123456"
            }
        )
        
        hash_with_none = self.hash_gen.generate_hash_from_metadata(data_with_none)
        hash_without_none = self.hash_gen.generate_hash_from_metadata(data_without_none)
        
        assert hash_with_none == hash_without_none, "None values in device_info should be filtered out"
    
    def test_create_hash_data_from_operation(self):
        """Test creating HashData from WipeResult."""
        wipe_result = WipeResult(
            operation_id="op_001",
            device_id="device_001",
            method=WipeMethod.NIST_PURGE,
            passes_completed=5,
            start_time=datetime(2026, 1, 8, 10, 0, 0),
            success=True,
            operator_id="test_operator",
            verification_hash="abc123"
        )
        
        # Without additional device info
        hash_data = self.hash_gen.create_hash_data_from_operation(wipe_result)
        
        assert hash_data.device_id == "device_001"
        assert hash_data.timestamp == "2026-01-08T10:00:00"
        assert hash_data.method == "purge"
        assert hash_data.passes == 5
        assert hash_data.operator == "test_operator"
        assert hash_data.verification_data == "abc123"
        assert hash_data.device_info is None
        
        # With additional device info
        device_info = {"manufacturer": "Test Corp", "model": "Test Model"}
        hash_data_with_info = self.hash_gen.create_hash_data_from_operation(wipe_result, device_info)
        
        assert hash_data_with_info.device_info == device_info
        
        # With None WipeResult
        with pytest.raises(ValueError, match="WipeResult cannot be None"):
            self.hash_gen.create_hash_data_from_operation(None)
    
    def test_get_hash_info_utility(self):
        """Test hash information utility function."""
        # Valid SHA-256 hash
        valid_hash = "a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456"
        info = self.hash_gen.get_hash_info(valid_hash)
        
        assert info['valid'] is True
        assert info['algorithm'] == 'sha256'
        assert info['length'] == 64
        assert info['format'] == 'hexadecimal'
        assert 'error' not in info
        
        # Invalid hash - too short
        short_hash = "abc123"
        info_short = self.hash_gen.get_hash_info(short_hash)
        
        assert info_short['valid'] is False
        assert info_short['length'] == 6
        assert 'error' in info_short
        
        # Invalid hash - wrong characters
        invalid_chars = "g" * 64
        info_invalid = self.hash_gen.get_hash_info(invalid_chars)
        
        assert info_invalid['valid'] is False
        assert info_invalid['format'] == 'invalid'
        assert 'error' in info_invalid
        
        # Empty hash
        info_empty = self.hash_gen.get_hash_info("")
        
        assert info_empty['valid'] is False
        assert 'error' in info_empty
        
        # Mixed case valid hash
        mixed_case_hash = "A1B2c3d4E5F6789012345678901234567890ABCDEF1234567890abcdef123456"
        info_mixed = self.hash_gen.get_hash_info(mixed_case_hash)
        
        assert info_mixed['valid'] is True
        assert info_mixed['format'] == 'hexadecimal'
    
    def test_hash_verification_case_insensitive(self):
        """Test that hash verification is case insensitive."""
        hash_data = HashData(
            device_id="device_001",
            timestamp="2026-01-08T10:00:00",
            method="clear",
            passes=3,
            operator="test_op"
        )
        
        original_hash = self.hash_gen.generate_hash_from_metadata(hash_data)
        
        # Test with uppercase
        assert self.hash_gen.verify_hash_from_metadata(hash_data, original_hash.upper())
        
        # Test with mixed case
        mixed_case = ''.join(c.upper() if i % 2 == 0 else c.lower() 
                           for i, c in enumerate(original_hash))
        assert self.hash_gen.verify_hash_from_metadata(hash_data, mixed_case)
        
        # Test with whitespace (should be stripped)
        assert self.hash_gen.verify_hash_from_metadata(hash_data, f"  {original_hash}  ")
    
    def test_hash_verification_failure_scenarios(self):
        """Test scenarios where hash verification should fail gracefully."""
        # Create valid data that will cause hash generation to fail
        invalid_wipe_result = WipeResult(
            operation_id="op_001",
            device_id="",  # Empty device ID will cause hash generation to fail
            method=WipeMethod.NIST_CLEAR,
            passes_completed=3,
            start_time=datetime.now(),
            success=True,
            operator_id="test_op"
        )
        
        # Verification should return False when hash generation fails
        result = self.hash_gen.verify_hash(invalid_wipe_result, "a" * 64)
        assert result is False, "Verification should return False when hash generation fails"
        
        # Same for metadata verification
        invalid_hash_data = HashData(
            device_id="",  # Empty device ID
            timestamp="2026-01-08T10:00:00",
            method="clear",
            passes=3,
            operator="test_op"
        )
        
        result = self.hash_gen.verify_hash_from_metadata(invalid_hash_data, "a" * 64)
        assert result is False, "Metadata verification should return False when hash generation fails"
    
    def test_specific_hash_values(self):
        """Test with specific known hash values for regression testing."""
        # Known test case
        test_data = HashData(
            device_id="TEST_DEVICE_001",
            timestamp="2026-01-08T10:00:00",
            method="clear",
            passes=3,
            operator="test_operator"
        )
        
        # Generate hash
        hash_value = self.hash_gen.generate_hash_from_metadata(test_data)
        
        # This should be deterministic - same input should always produce same hash
        expected_hash = self.hash_gen.generate_hash_from_metadata(test_data)
        assert hash_value == expected_hash
        
        # Verify the hash
        assert self.hash_gen.verify_hash_from_metadata(test_data, hash_value)
        
        # Ensure it's a valid SHA-256 format
        assert len(hash_value) == 64
        assert all(c in '0123456789abcdef' for c in hash_value)
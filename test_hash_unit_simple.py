#!/usr/bin/env python3
"""
Simple unit tests for HashGenerator without pytest dependency.
"""

import sys
import os
from datetime import datetime

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from secure_data_wiping.hash_generator import HashGenerator
from secure_data_wiping.utils.data_models import HashData, WipeResult, WipeMethod


def test_hash_generator_initialization():
    """Test HashGenerator initialization."""
    print("Testing HashGenerator initialization...")
    
    # Default initialization
    hash_gen = HashGenerator()
    assert hash_gen.get_algorithm() == "sha256"
    
    # Explicit SHA-256 initialization
    hash_gen_explicit = HashGenerator("sha256")
    assert hash_gen_explicit.get_algorithm() == "sha256"
    
    # Case insensitive
    hash_gen_upper = HashGenerator("SHA256")
    assert hash_gen_upper.get_algorithm() == "sha256"
    
    print("✓ Initialization tests passed")


def test_unsupported_algorithm_rejection():
    """Test that unsupported algorithms are rejected."""
    print("Testing unsupported algorithm rejection...")
    
    unsupported_algorithms = ["md5", "sha1", "sha512", "blake2b", "invalid"]
    
    for algorithm in unsupported_algorithms:
        try:
            HashGenerator(algorithm)
            assert False, f"Should have rejected {algorithm}"
        except ValueError as e:
            assert "Unsupported algorithm" in str(e)
    
    print("✓ Unsupported algorithm rejection tests passed")


def test_missing_fields_error_handling():
    """Test hash generation with missing required fields."""
    print("Testing missing fields error handling...")
    
    hash_gen = HashGenerator()
    
    # Missing device_id
    try:
        hash_data = HashData(
            device_id="",
            timestamp="2026-01-08T10:00:00",
            method="clear",
            passes=3,
            operator="test_op"
        )
        hash_gen.generate_hash_from_metadata(hash_data)
        assert False, "Should have failed with empty device_id"
    except ValueError as e:
        assert "device_id" in str(e)
    
    # None input
    try:
        hash_gen.generate_hash_from_metadata(None)
        assert False, "Should have failed with None input"
    except ValueError as e:
        assert "HashData cannot be None" in str(e)
    
    print("✓ Missing fields error handling tests passed")


def test_wipe_result_invalid_inputs():
    """Test wipe hash generation with invalid inputs."""
    print("Testing WipeResult invalid inputs...")
    
    hash_gen = HashGenerator()
    
    # None input
    try:
        hash_gen.generate_wipe_hash(None)
        assert False, "Should have failed with None input"
    except ValueError as e:
        assert "WipeResult cannot be None" in str(e)
    
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
    
    try:
        hash_gen.generate_wipe_hash(wipe_result)
        assert False, "Should have failed with failed operation"
    except ValueError as e:
        assert "Cannot generate hash for failed wiping operation" in str(e)
    
    print("✓ WipeResult invalid inputs tests passed")


def test_hash_verification_invalid_inputs():
    """Test hash verification with invalid inputs."""
    print("Testing hash verification invalid inputs...")
    
    hash_gen = HashGenerator()
    
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
    try:
        hash_gen.verify_hash(valid_wipe_result, "")
        assert False, "Should have failed with empty hash"
    except ValueError as e:
        assert "Expected hash cannot be empty" in str(e)
    
    # Invalid hash length
    try:
        hash_gen.verify_hash(valid_wipe_result, "a" * 63)  # Too short
        assert False, "Should have failed with invalid hash length"
    except ValueError as e:
        assert "Invalid hash length" in str(e)
    
    # Invalid hex characters
    try:
        hash_gen.verify_hash(valid_wipe_result, "g" * 64)  # Invalid hex
        assert False, "Should have failed with invalid hex characters"
    except ValueError as e:
        assert "Invalid hash format" in str(e)
    
    print("✓ Hash verification invalid inputs tests passed")


def test_optional_fields():
    """Test hash generation with optional fields."""
    print("Testing optional fields...")
    
    hash_gen = HashGenerator()
    
    # Base data without optional fields
    base_data = HashData(
        device_id="device_001",
        timestamp="2026-01-08T10:00:00",
        method="clear",
        passes=3,
        operator="test_op"
    )
    
    base_hash = hash_gen.generate_hash_from_metadata(base_data)
    
    # Data with verification_data
    data_with_verification = HashData(
        device_id="device_001",
        timestamp="2026-01-08T10:00:00",
        method="clear",
        passes=3,
        operator="test_op",
        verification_data="verification_hash_123"
    )
    
    verification_hash = hash_gen.generate_hash_from_metadata(data_with_verification)
    assert base_hash != verification_hash, "Hash should change when verification_data is added"
    
    print("✓ Optional fields tests passed")


def test_device_info_ordering_consistency():
    """Test that device_info dictionary ordering doesn't affect hash."""
    print("Testing device_info ordering consistency...")
    
    hash_gen = HashGenerator()
    
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
    
    hash1 = hash_gen.generate_hash_from_metadata(data1)
    hash2 = hash_gen.generate_hash_from_metadata(data2)
    
    assert hash1 == hash2, "Hash should be consistent regardless of device_info key ordering"
    
    print("✓ Device info ordering consistency tests passed")


def test_hash_info_utility():
    """Test hash information utility function."""
    print("Testing hash info utility...")
    
    hash_gen = HashGenerator()
    
    # Valid SHA-256 hash
    valid_hash = "a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456"
    info = hash_gen.get_hash_info(valid_hash)
    
    assert info['valid'] is True
    assert info['algorithm'] == 'sha256'
    assert info['length'] == 64
    assert info['format'] == 'hexadecimal'
    
    # Invalid hash - too short
    short_hash = "abc123"
    info_short = hash_gen.get_hash_info(short_hash)
    
    assert info_short['valid'] is False
    assert info_short['length'] == 6
    assert 'error' in info_short
    
    print("✓ Hash info utility tests passed")


def test_case_insensitive_verification():
    """Test that hash verification is case insensitive."""
    print("Testing case insensitive verification...")
    
    hash_gen = HashGenerator()
    
    hash_data = HashData(
        device_id="device_001",
        timestamp="2026-01-08T10:00:00",
        method="clear",
        passes=3,
        operator="test_op"
    )
    
    original_hash = hash_gen.generate_hash_from_metadata(hash_data)
    
    # Test with uppercase
    assert hash_gen.verify_hash_from_metadata(hash_data, original_hash.upper())
    
    # Test with whitespace (should be stripped)
    assert hash_gen.verify_hash_from_metadata(hash_data, f"  {original_hash}  ")
    
    print("✓ Case insensitive verification tests passed")


def test_create_hash_data_from_operation():
    """Test creating HashData from WipeResult."""
    print("Testing create_hash_data_from_operation...")
    
    hash_gen = HashGenerator()
    
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
    hash_data = hash_gen.create_hash_data_from_operation(wipe_result)
    
    assert hash_data.device_id == "device_001"
    assert hash_data.timestamp == "2026-01-08T10:00:00"
    assert hash_data.method == "purge"
    assert hash_data.passes == 5
    assert hash_data.operator == "test_operator"
    assert hash_data.verification_data == "abc123"
    assert hash_data.device_info is None
    
    # With additional device info
    device_info = {"manufacturer": "Test Corp", "model": "Test Model"}
    hash_data_with_info = hash_gen.create_hash_data_from_operation(wipe_result, device_info)
    
    assert hash_data_with_info.device_info == device_info
    
    print("✓ create_hash_data_from_operation tests passed")


if __name__ == "__main__":
    try:
        test_hash_generator_initialization()
        test_unsupported_algorithm_rejection()
        test_missing_fields_error_handling()
        test_wipe_result_invalid_inputs()
        test_hash_verification_invalid_inputs()
        test_optional_fields()
        test_device_info_ordering_consistency()
        test_hash_info_utility()
        test_case_insensitive_verification()
        test_create_hash_data_from_operation()
        print("\n🎉 All HashGenerator unit tests passed successfully!")
        print("✓ Task 3.4: Unit tests for hash generation edge cases - COMPLETED")
    except Exception as e:
        print(f"\n❌ Unit test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
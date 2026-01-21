#!/usr/bin/env python3
"""
Simple test for HashGenerator implementation.
Tests basic functionality without property-based testing.
"""

import sys
import os
from datetime import datetime

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from secure_data_wiping.hash_generator import HashGenerator
from secure_data_wiping.utils.data_models import HashData, WipeResult, WipeMethod


def test_hash_generator_basic():
    """Test basic hash generation functionality."""
    print("Testing HashGenerator basic functionality...")
    
    # Create hash generator
    hash_gen = HashGenerator()
    
    # Test 1: Create HashData and generate hash
    hash_data = HashData(
        device_id="TEST_DEVICE_001",
        timestamp="2026-01-08T10:00:00",
        method="clear",
        passes=3,
        operator="test_operator"
    )
    
    hash_value = hash_gen.generate_hash_from_metadata(hash_data)
    print(f"Generated hash: {hash_value}")
    
    # Verify hash format
    assert len(hash_value) == 64, f"Hash length should be 64, got {len(hash_value)}"
    assert all(c in '0123456789abcdef' for c in hash_value), "Hash should contain only hex characters"
    
    # Test 2: Hash determinism - same data should produce same hash
    hash_value2 = hash_gen.generate_hash_from_metadata(hash_data)
    assert hash_value == hash_value2, "Same data should produce identical hashes"
    print("✓ Hash determinism test passed")
    
    # Test 3: Hash verification
    is_valid = hash_gen.verify_hash_from_metadata(hash_data, hash_value)
    assert is_valid, "Hash verification should succeed for correct hash"
    print("✓ Hash verification test passed")
    
    # Test 4: Tamper detection
    tampered_data = HashData(
        device_id="TAMPERED_DEVICE_001",  # Changed device ID
        timestamp="2026-01-08T10:00:00",
        method="clear",
        passes=3,
        operator="test_operator"
    )
    
    is_tampered = hash_gen.verify_hash_from_metadata(tampered_data, hash_value)
    assert not is_tampered, "Hash verification should fail for tampered data"
    print("✓ Tamper detection test passed")
    
    print("All basic HashGenerator tests passed!")


def test_wipe_result_hash_generation():
    """Test hash generation from WipeResult."""
    print("\nTesting WipeResult hash generation...")
    
    hash_gen = HashGenerator()
    
    # Create a WipeResult
    wipe_result = WipeResult(
        operation_id="op_001",
        device_id="TEST_DEVICE_002",
        method=WipeMethod.NIST_CLEAR,
        passes_completed=3,
        start_time=datetime(2026, 1, 8, 10, 0, 0),
        end_time=datetime(2026, 1, 8, 10, 30, 0),
        success=True,
        operator_id="test_operator"
    )
    
    # Generate hash from WipeResult
    hash_value = hash_gen.generate_wipe_hash(wipe_result)
    print(f"WipeResult hash: {hash_value}")
    
    # Verify hash format
    assert len(hash_value) == 64, f"Hash length should be 64, got {len(hash_value)}"
    
    # Test verification
    is_valid = hash_gen.verify_hash(wipe_result, hash_value)
    assert is_valid, "Hash verification should succeed for WipeResult"
    print("✓ WipeResult hash generation and verification passed")


def test_error_handling():
    """Test error handling in HashGenerator."""
    print("\nTesting error handling...")
    
    hash_gen = HashGenerator()
    
    # Test invalid algorithm
    try:
        HashGenerator("md5")
        assert False, "Should raise ValueError for unsupported algorithm"
    except ValueError as e:
        print(f"✓ Correctly rejected unsupported algorithm: {e}")
    
    # Test None input
    try:
        hash_gen.generate_hash_from_metadata(None)
        assert False, "Should raise ValueError for None input"
    except ValueError as e:
        print(f"✓ Correctly rejected None input: {e}")
    
    # Test missing required field
    incomplete_data = HashData(
        device_id="",  # Empty device ID
        timestamp="2026-01-08T10:00:00",
        method="clear",
        passes=3,
        operator="test_operator"
    )
    
    try:
        hash_gen.generate_hash_from_metadata(incomplete_data)
        assert False, "Should raise ValueError for empty device_id"
    except ValueError as e:
        print(f"✓ Correctly rejected empty device_id: {e}")
    
    print("All error handling tests passed!")


def test_hash_info():
    """Test hash information utility."""
    print("\nTesting hash info utility...")
    
    hash_gen = HashGenerator()
    
    # Valid hash
    valid_hash = "a" * 64  # 64 hex characters
    info = hash_gen.get_hash_info(valid_hash)
    assert info['valid'], "Should recognize valid hash"
    assert info['algorithm'] == 'sha256', "Should report correct algorithm"
    print("✓ Valid hash info test passed")
    
    # Invalid hash
    invalid_hash = "xyz123"
    info = hash_gen.get_hash_info(invalid_hash)
    assert not info['valid'], "Should recognize invalid hash"
    print("✓ Invalid hash info test passed")


if __name__ == "__main__":
    try:
        test_hash_generator_basic()
        test_wipe_result_hash_generation()
        test_error_handling()
        test_hash_info()
        print("\n🎉 All HashGenerator tests passed successfully!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
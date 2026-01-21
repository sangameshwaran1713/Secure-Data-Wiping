#!/usr/bin/env python3
"""
Simple property-like tests for HashGenerator without using hypothesis.
Tests the key properties manually with multiple test cases.
"""

import sys
import os
from datetime import datetime, timedelta
import random
import string

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from secure_data_wiping.hash_generator import HashGenerator
from secure_data_wiping.utils.data_models import HashData, WipeResult, WipeMethod


def generate_random_hash_data():
    """Generate random HashData for testing."""
    device_id = ''.join(random.choices(string.ascii_letters + string.digits, k=random.randint(5, 20)))
    timestamp = datetime.now().isoformat()
    method = random.choice(['clear', 'purge', 'destroy'])
    passes = random.randint(1, 10)
    operator = ''.join(random.choices(string.ascii_letters + string.digits, k=random.randint(5, 15)))
    
    return HashData(
        device_id=device_id,
        timestamp=timestamp,
        method=method,
        passes=passes,
        operator=operator
    )


def test_property_2_hash_generation_completeness_and_determinism():
    """
    Property 2: Hash Generation Completeness and Determinism
    
    For any completed wiping operation, the system should generate a SHA-256 hash 
    that includes device identifier, timestamp, and wiping parameters, and identical 
    operations should always produce identical hashes.
    """
    print("Testing Property 2: Hash Generation Completeness and Determinism")
    
    hash_gen = HashGenerator()
    
    # Test with multiple random data sets
    for i in range(20):
        hash_data = generate_random_hash_data()
        
        # Generate hash from the data
        hash_value = hash_gen.generate_hash_from_metadata(hash_data)
        
        # Property: Hash should be a valid SHA-256 (64 hex characters)
        assert len(hash_value) == 64, f"Hash should be 64 characters, got {len(hash_value)}"
        assert all(c in '0123456789abcdef' for c in hash_value), "Hash should contain only hex characters"
        
        # Test determinism: identical data should produce identical hashes
        hash_value2 = hash_gen.generate_hash_from_metadata(hash_data)
        assert hash_value == hash_value2, "Identical data should produce identical hashes"
        
        # Test completeness: hash should change when device_id changes
        modified_data = HashData(
            device_id=hash_data.device_id + "_modified",
            timestamp=hash_data.timestamp,
            method=hash_data.method,
            passes=hash_data.passes,
            operator=hash_data.operator
        )
        
        modified_hash = hash_gen.generate_hash_from_metadata(modified_data)
        assert hash_value != modified_hash, f"Hash should change when device_id changes (iteration {i})"
        
        # Test completeness: hash should change when method changes
        different_methods = ['clear', 'purge', 'destroy']
        different_methods.remove(hash_data.method)
        
        method_modified_data = HashData(
            device_id=hash_data.device_id,
            timestamp=hash_data.timestamp,
            method=different_methods[0],
            passes=hash_data.passes,
            operator=hash_data.operator
        )
        
        method_modified_hash = hash_gen.generate_hash_from_metadata(method_modified_data)
        assert hash_value != method_modified_hash, f"Hash should change when method changes (iteration {i})"
        
        # Test completeness: hash should change when passes change
        passes_modified_data = HashData(
            device_id=hash_data.device_id,
            timestamp=hash_data.timestamp,
            method=hash_data.method,
            passes=hash_data.passes + 1,
            operator=hash_data.operator
        )
        
        passes_modified_hash = hash_gen.generate_hash_from_metadata(passes_modified_data)
        assert hash_value != passes_modified_hash, f"Hash should change when passes change (iteration {i})"
    
    print("✓ Property 2 test passed with 20 random test cases")


def test_property_3_tamper_detection_through_hash_verification():
    """
    Property 3: Tamper Detection Through Hash Verification
    
    For any wiping operation data, if the data is modified after hash generation, 
    the system should detect the tampering through hash comparison.
    """
    print("Testing Property 3: Tamper Detection Through Hash Verification")
    
    hash_gen = HashGenerator()
    
    # Test with multiple random data sets
    for i in range(20):
        hash_data = generate_random_hash_data()
        
        # Generate original hash
        original_hash = hash_gen.generate_hash_from_metadata(hash_data)
        
        # Property: Original data should verify successfully
        assert hash_gen.verify_hash_from_metadata(hash_data, original_hash), \
            f"Original data should verify successfully against its hash (iteration {i})"
        
        # Property: Tampered device_id should fail verification
        tampered_device_data = HashData(
            device_id=hash_data.device_id + "_tampered",
            timestamp=hash_data.timestamp,
            method=hash_data.method,
            passes=hash_data.passes,
            operator=hash_data.operator
        )
        
        assert not hash_gen.verify_hash_from_metadata(tampered_device_data, original_hash), \
            f"Tampered device_id should fail hash verification (iteration {i})"
        
        # Property: Tampered passes should fail verification
        tampered_passes_data = HashData(
            device_id=hash_data.device_id,
            timestamp=hash_data.timestamp,
            method=hash_data.method,
            passes=hash_data.passes + 1,
            operator=hash_data.operator
        )
        
        assert not hash_gen.verify_hash_from_metadata(tampered_passes_data, original_hash), \
            f"Tampered passes should fail hash verification (iteration {i})"
        
        # Property: Tampered operator should fail verification
        tampered_operator_data = HashData(
            device_id=hash_data.device_id,
            timestamp=hash_data.timestamp,
            method=hash_data.method,
            passes=hash_data.passes,
            operator=hash_data.operator + "_tampered"
        )
        
        assert not hash_gen.verify_hash_from_metadata(tampered_operator_data, original_hash), \
            f"Tampered operator should fail hash verification (iteration {i})"
        
        # Property: Invalid hash format should fail verification
        invalid_hashes = [
            "invalid_hash",  # Wrong format
            "a" * 63,       # Too short
            "a" * 65,       # Too long
            "",             # Empty
            "g" * 64        # Invalid hex characters
        ]
        
        for invalid_hash in invalid_hashes:
            try:
                result = hash_gen.verify_hash_from_metadata(hash_data, invalid_hash)
                assert not result, f"Invalid hash '{invalid_hash}' should fail verification (iteration {i})"
            except ValueError:
                # ValueError is also acceptable for invalid hash formats
                pass
    
    print("✓ Property 3 test passed with 20 random test cases")


def test_wipe_result_hash_determinism():
    """Test hash determinism specifically for WipeResult objects."""
    print("Testing WipeResult hash determinism")
    
    hash_gen = HashGenerator()
    
    # Test with multiple WipeResult objects
    for i in range(10):
        wipe_result = WipeResult(
            operation_id=f"op_{i:03d}",
            device_id=f"device_{i:03d}",
            method=random.choice([WipeMethod.NIST_CLEAR, WipeMethod.NIST_PURGE, WipeMethod.NIST_DESTROY]),
            passes_completed=random.randint(1, 5),
            start_time=datetime.now() - timedelta(hours=i),
            end_time=datetime.now() - timedelta(hours=i) + timedelta(minutes=30),
            success=True,
            operator_id=f"operator_{i}"
        )
        
        # Generate hash twice from the same WipeResult
        hash1 = hash_gen.generate_wipe_hash(wipe_result)
        hash2 = hash_gen.generate_wipe_hash(wipe_result)
        
        # Property: Same WipeResult should produce identical hashes
        assert hash1 == hash2, f"Same WipeResult should produce identical hashes (iteration {i})"
        
        # Property: Hash should be valid SHA-256 format
        assert len(hash1) == 64, f"Hash should be 64 characters, got {len(hash1)} (iteration {i})"
        assert all(c in '0123456789abcdef' for c in hash1), f"Hash should contain only hex characters (iteration {i})"
        
        # Property: Hash verification should succeed for original data
        assert hash_gen.verify_hash(wipe_result, hash1), \
            f"Hash verification should succeed for original WipeResult (iteration {i})"
    
    print("✓ WipeResult hash determinism test passed with 10 test cases")


def test_hash_data_serialization_consistency():
    """Test that hash generation is consistent across different serialization approaches."""
    print("Testing hash data serialization consistency")
    
    hash_gen = HashGenerator()
    
    for i in range(10):
        hash_data = generate_random_hash_data()
        
        # Generate hash multiple times
        hashes = [hash_gen.generate_hash_from_metadata(hash_data) for _ in range(3)]
        
        # Property: All hashes should be identical
        assert all(h == hashes[0] for h in hashes), \
            f"Multiple hash generations should produce identical results (iteration {i})"
        
        # Property: Hash should not depend on object identity
        # Create a new HashData with identical values
        hash_data_copy = HashData(
            device_id=hash_data.device_id,
            timestamp=hash_data.timestamp,
            method=hash_data.method,
            passes=hash_data.passes,
            operator=hash_data.operator,
            verification_data=hash_data.verification_data,
            device_info=hash_data.device_info.copy() if hash_data.device_info else None
        )
        
        copy_hash = hash_gen.generate_hash_from_metadata(hash_data_copy)
        assert copy_hash == hashes[0], \
            f"Hash should not depend on object identity, only on values (iteration {i})"
    
    print("✓ Hash data serialization consistency test passed with 10 test cases")


def test_edge_cases():
    """Test edge cases for hash generation."""
    print("Testing edge cases")
    
    hash_gen = HashGenerator()
    
    # Test with minimal valid data
    minimal_data = HashData(
        device_id="a",
        timestamp="2026-01-08T10:00:00",
        method="clear",
        passes=1,
        operator="op"
    )
    
    hash_value = hash_gen.generate_hash_from_metadata(minimal_data)
    assert len(hash_value) == 64, "Minimal data should produce valid hash"
    
    # Test with maximum reasonable data
    max_data = HashData(
        device_id="a" * 50,
        timestamp="2026-01-08T10:00:00.123456",
        method="destroy",
        passes=10,
        operator="operator_with_long_name_12345",
        verification_data="verification_hash_data_12345",
        device_info={
            "manufacturer": "Test Manufacturer",
            "model": "Test Model 12345",
            "serial": "SN123456789",
            "capacity": 1000000000
        }
    )
    
    max_hash = hash_gen.generate_hash_from_metadata(max_data)
    assert len(max_hash) == 64, "Maximum data should produce valid hash"
    
    # Ensure different data produces different hashes
    assert hash_value != max_hash, "Different data should produce different hashes"
    
    print("✓ Edge cases test passed")


if __name__ == "__main__":
    try:
        test_property_2_hash_generation_completeness_and_determinism()
        test_property_3_tamper_detection_through_hash_verification()
        test_wipe_result_hash_determinism()
        test_hash_data_serialization_consistency()
        test_edge_cases()
        print("\n🎉 All HashGenerator property tests passed successfully!")
        print("✓ Property 2: Hash Generation Completeness and Determinism - VALIDATED")
        print("✓ Property 3: Tamper Detection Through Hash Verification - VALIDATED")
    except Exception as e:
        print(f"\n❌ Property test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
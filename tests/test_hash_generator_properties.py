"""
Property-based tests for Hash Generator component.

Tests universal properties of hash generation including determinism and tamper detection.
"""

import pytest
from hypothesis import given, strategies as st, assume, settings
from datetime import datetime, timedelta
import json
from typing import Dict, Any

from secure_data_wiping.hash_generator import HashGenerator
from secure_data_wiping.utils.data_models import HashData, WipeResult, WipeMethod


# Test data generation strategies
@st.composite
def hash_data_strategy(draw):
    """Generate valid HashData for property testing."""
    device_id = draw(st.text(min_size=1, max_size=50, alphabet=st.characters(
        whitelist_categories=('Lu', 'Ll', 'Nd'), 
        whitelist_characters='_-'
    )))
    
    # Generate timestamp in ISO format
    base_time = datetime(2020, 1, 1)
    time_offset = draw(st.integers(min_value=0, max_value=365*24*3600))  # Up to 1 year
    timestamp = (base_time + timedelta(seconds=time_offset)).isoformat()
    
    method = draw(st.sampled_from(['clear', 'purge', 'destroy']))
    passes = draw(st.integers(min_value=1, max_value=10))
    operator = draw(st.text(min_size=1, max_size=30, alphabet=st.characters(
        whitelist_categories=('Lu', 'Ll', 'Nd'),
        whitelist_characters='_-@.'
    )))
    
    # Optional verification data
    verification_data = draw(st.one_of(
        st.none(),
        st.text(min_size=1, max_size=100, alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll', 'Nd'),
            whitelist_characters='_-'
        ))
    ))
    
    # Optional device info
    device_info = draw(st.one_of(
        st.none(),
        st.dictionaries(
            keys=st.sampled_from(['manufacturer', 'model', 'serial', 'capacity']),
            values=st.one_of(
                st.text(min_size=1, max_size=20),
                st.integers(min_value=1, max_value=1000000)
            ),
            min_size=0,
            max_size=4
        )
    ))
    
    return HashData(
        device_id=device_id,
        timestamp=timestamp,
        method=method,
        passes=passes,
        operator=operator,
        verification_data=verification_data,
        device_info=device_info
    )


@st.composite
def wipe_result_strategy(draw):
    """Generate valid WipeResult for property testing."""
    operation_id = draw(st.text(min_size=1, max_size=50, alphabet=st.characters(
        whitelist_categories=('Lu', 'Ll', 'Nd'),
        whitelist_characters='_-'
    )))
    
    device_id = draw(st.text(min_size=1, max_size=50, alphabet=st.characters(
        whitelist_categories=('Lu', 'Ll', 'Nd'),
        whitelist_characters='_-'
    )))
    
    method = draw(st.sampled_from([WipeMethod.NIST_CLEAR, WipeMethod.NIST_PURGE, WipeMethod.NIST_DESTROY]))
    passes_completed = draw(st.integers(min_value=1, max_value=10))
    
    # Generate start time
    base_time = datetime(2020, 1, 1)
    time_offset = draw(st.integers(min_value=0, max_value=365*24*3600))
    start_time = base_time + timedelta(seconds=time_offset)
    
    # End time after start time
    duration = draw(st.integers(min_value=60, max_value=3600))  # 1 minute to 1 hour
    end_time = start_time + timedelta(seconds=duration)
    
    operator_id = draw(st.text(min_size=1, max_size=30, alphabet=st.characters(
        whitelist_categories=('Lu', 'Ll', 'Nd'),
        whitelist_characters='_-@.'
    )))
    
    verification_hash = draw(st.one_of(
        st.none(),
        st.text(min_size=64, max_size=64, alphabet='0123456789abcdef')
    ))
    
    return WipeResult(
        operation_id=operation_id,
        device_id=device_id,
        method=method,
        passes_completed=passes_completed,
        start_time=start_time,
        end_time=end_time,
        success=True,  # Only test successful operations for hash generation
        operator_id=operator_id,
        verification_hash=verification_hash
    )


class TestHashGeneratorProperties:
    """Property-based tests for HashGenerator."""
    
    @given(hash_data=hash_data_strategy())
    @settings(max_examples=100, deadline=None)
    def test_property_2_hash_generation_completeness_and_determinism(self, hash_data):
        """
        Feature: secure-data-wiping-blockchain
        Property 2: Hash Generation Completeness and Determinism
        
        For any completed wiping operation, the system should generate a SHA-256 hash 
        that includes device identifier, timestamp, and wiping parameters, and identical 
        operations should always produce identical hashes.
        
        Validates: Requirements 2.1, 2.2, 2.4
        """
        hash_gen = HashGenerator()
        
        # Generate hash from the data
        hash_value = hash_gen.generate_hash_from_metadata(hash_data)
        
        # Property: Hash should be a valid SHA-256 (64 hex characters)
        assert len(hash_value) == 64, f"Hash should be 64 characters, got {len(hash_value)}"
        assert all(c in '0123456789abcdef' for c in hash_value), "Hash should contain only hex characters"
        
        # Property: Hash should include all required metadata
        # We verify this by checking that the hash changes when any required field changes
        
        # Test determinism: identical data should produce identical hashes
        hash_value2 = hash_gen.generate_hash_from_metadata(hash_data)
        assert hash_value == hash_value2, "Identical data should produce identical hashes"
        
        # Test completeness: hash should change when device_id changes
        modified_data = HashData(
            device_id=hash_data.device_id + "_modified",
            timestamp=hash_data.timestamp,
            method=hash_data.method,
            passes=hash_data.passes,
            operator=hash_data.operator,
            verification_data=hash_data.verification_data,
            device_info=hash_data.device_info
        )
        
        modified_hash = hash_gen.generate_hash_from_metadata(modified_data)
        assert hash_value != modified_hash, "Hash should change when device_id changes"
        
        # Test completeness: hash should change when timestamp changes
        # Modify timestamp by adding one second
        try:
            original_dt = datetime.fromisoformat(hash_data.timestamp.replace('Z', '+00:00'))
            modified_dt = original_dt + timedelta(seconds=1)
            modified_timestamp = modified_dt.isoformat()
            
            timestamp_modified_data = HashData(
                device_id=hash_data.device_id,
                timestamp=modified_timestamp,
                method=hash_data.method,
                passes=hash_data.passes,
                operator=hash_data.operator,
                verification_data=hash_data.verification_data,
                device_info=hash_data.device_info
            )
            
            timestamp_modified_hash = hash_gen.generate_hash_from_metadata(timestamp_modified_data)
            assert hash_value != timestamp_modified_hash, "Hash should change when timestamp changes"
        except ValueError:
            # If timestamp parsing fails, skip this specific check
            pass
        
        # Test completeness: hash should change when method changes
        different_methods = ['clear', 'purge', 'destroy']
        different_methods.remove(hash_data.method)
        if different_methods:
            method_modified_data = HashData(
                device_id=hash_data.device_id,
                timestamp=hash_data.timestamp,
                method=different_methods[0],
                passes=hash_data.passes,
                operator=hash_data.operator,
                verification_data=hash_data.verification_data,
                device_info=hash_data.device_info
            )
            
            method_modified_hash = hash_gen.generate_hash_from_metadata(method_modified_data)
            assert hash_value != method_modified_hash, "Hash should change when method changes"
    
    @given(hash_data=hash_data_strategy())
    @settings(max_examples=100, deadline=None)
    def test_property_3_tamper_detection_through_hash_verification(self, hash_data):
        """
        Feature: secure-data-wiping-blockchain
        Property 3: Tamper Detection Through Hash Verification
        
        For any wiping operation data, if the data is modified after hash generation, 
        the system should detect the tampering through hash comparison.
        
        Validates: Requirements 2.5
        """
        hash_gen = HashGenerator()
        
        # Generate original hash
        original_hash = hash_gen.generate_hash_from_metadata(hash_data)
        
        # Property: Original data should verify successfully
        assert hash_gen.verify_hash_from_metadata(hash_data, original_hash), \
            "Original data should verify successfully against its hash"
        
        # Property: Tampered device_id should fail verification
        tampered_device_data = HashData(
            device_id=hash_data.device_id + "_tampered",
            timestamp=hash_data.timestamp,
            method=hash_data.method,
            passes=hash_data.passes,
            operator=hash_data.operator,
            verification_data=hash_data.verification_data,
            device_info=hash_data.device_info
        )
        
        assert not hash_gen.verify_hash_from_metadata(tampered_device_data, original_hash), \
            "Tampered device_id should fail hash verification"
        
        # Property: Tampered passes should fail verification
        tampered_passes_data = HashData(
            device_id=hash_data.device_id,
            timestamp=hash_data.timestamp,
            method=hash_data.method,
            passes=hash_data.passes + 1,  # Change number of passes
            operator=hash_data.operator,
            verification_data=hash_data.verification_data,
            device_info=hash_data.device_info
        )
        
        assert not hash_gen.verify_hash_from_metadata(tampered_passes_data, original_hash), \
            "Tampered passes should fail hash verification"
        
        # Property: Tampered operator should fail verification
        tampered_operator_data = HashData(
            device_id=hash_data.device_id,
            timestamp=hash_data.timestamp,
            method=hash_data.method,
            passes=hash_data.passes,
            operator=hash_data.operator + "_tampered",
            verification_data=hash_data.verification_data,
            device_info=hash_data.device_info
        )
        
        assert not hash_gen.verify_hash_from_metadata(tampered_operator_data, original_hash), \
            "Tampered operator should fail hash verification"
        
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
                assert not result, f"Invalid hash '{invalid_hash}' should fail verification"
            except ValueError:
                # ValueError is also acceptable for invalid hash formats
                pass
    
    @given(wipe_result=wipe_result_strategy())
    @settings(max_examples=50, deadline=None)
    def test_wipe_result_hash_determinism(self, wipe_result):
        """
        Test hash determinism specifically for WipeResult objects.
        
        This ensures that WipeResult hash generation is also deterministic.
        """
        hash_gen = HashGenerator()
        
        # Generate hash twice from the same WipeResult
        hash1 = hash_gen.generate_wipe_hash(wipe_result)
        hash2 = hash_gen.generate_wipe_hash(wipe_result)
        
        # Property: Same WipeResult should produce identical hashes
        assert hash1 == hash2, "Same WipeResult should produce identical hashes"
        
        # Property: Hash should be valid SHA-256 format
        assert len(hash1) == 64, f"Hash should be 64 characters, got {len(hash1)}"
        assert all(c in '0123456789abcdef' for c in hash1), "Hash should contain only hex characters"
        
        # Property: Hash verification should succeed for original data
        assert hash_gen.verify_hash(wipe_result, hash1), \
            "Hash verification should succeed for original WipeResult"
    
    @given(hash_data=hash_data_strategy())
    @settings(max_examples=50, deadline=None)
    def test_hash_data_serialization_consistency(self, hash_data):
        """
        Test that hash generation is consistent across different serialization approaches.
        
        This ensures that the internal JSON serialization is deterministic.
        """
        hash_gen = HashGenerator()
        
        # Generate hash multiple times
        hashes = [hash_gen.generate_hash_from_metadata(hash_data) for _ in range(3)]
        
        # Property: All hashes should be identical
        assert all(h == hashes[0] for h in hashes), \
            "Multiple hash generations should produce identical results"
        
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
            "Hash should not depend on object identity, only on values"
    
    def test_hash_generator_algorithm_consistency(self):
        """
        Test that HashGenerator consistently uses SHA-256 algorithm.
        """
        hash_gen = HashGenerator()
        
        # Property: Algorithm should be SHA-256
        assert hash_gen.get_algorithm() == "sha256", "Algorithm should be SHA-256"
        
        # Property: Should reject unsupported algorithms
        with pytest.raises(ValueError, match="Unsupported algorithm"):
            HashGenerator("md5")
        
        with pytest.raises(ValueError, match="Unsupported algorithm"):
            HashGenerator("sha1")
    
    @given(st.text(min_size=1, max_size=100))
    @settings(max_examples=50, deadline=None)
    def test_hash_info_utility_properties(self, test_string):
        """
        Test properties of the hash info utility function.
        """
        hash_gen = HashGenerator()
        
        # Test with valid SHA-256 hash (64 hex characters)
        valid_hash = "a" * 64
        info = hash_gen.get_hash_info(valid_hash)
        
        # Property: Valid hash should be recognized as valid
        assert info['valid'] is True, "Valid hash should be recognized as valid"
        assert info['algorithm'] == 'sha256', "Should report correct algorithm"
        assert info['length'] == 64, "Should report correct length"
        assert info['format'] == 'hexadecimal', "Should recognize hex format"
        
        # Test with invalid hash
        info_invalid = hash_gen.get_hash_info(test_string)
        
        # Property: Invalid hash should be recognized as invalid (unless it happens to be 64 hex chars)
        if len(test_string) == 64 and all(c in '0123456789abcdefABCDEF' for c in test_string):
            assert info_invalid['valid'] is True, "64 hex characters should be valid"
        else:
            assert info_invalid['valid'] is False, "Non-64-hex strings should be invalid"
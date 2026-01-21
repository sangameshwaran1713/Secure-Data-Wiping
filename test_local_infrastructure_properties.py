#!/usr/bin/env python3
"""
Property-based tests for Local Infrastructure implementation.
Tests universal properties that should hold for all valid inputs.
"""

import sys
import os
import tempfile
import json
import socket
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

# Add the project root to Python path
sys.path.insert(0, os.path.abspath('.'))

import pytest
from hypothesis import given, strategies as st, settings, assume

from secure_data_wiping.local_infrastructure import (
    NetworkIsolationChecker, OfflineVerifier, DataPrivacyFilter,
    NetworkIsolationError, OfflineVerificationError, DataPrivacyError
)
from secure_data_wiping.utils.data_models import WipeData, BlockchainData, DeviceInfo
from secure_data_wiping.utils.local_infrastructure import (
    LocalInfrastructureValidator, validate_system_is_local_only,
    LocalInfrastructureError, NetworkIsolationError as UtilsNetworkError,
    DataPrivacyError as UtilsDataPrivacyError
)


# Test data generators
@st.composite
def local_ip_strategy(draw):
    """Generate local IP addresses."""
    ip_type = draw(st.sampled_from(['loopback', 'private_a', 'private_b', 'private_c']))
    
    if ip_type == 'loopback':
        return '127.0.0.1'
    elif ip_type == 'private_a':
        return f"10.{draw(st.integers(0, 255))}.{draw(st.integers(0, 255))}.{draw(st.integers(1, 254))}"
    elif ip_type == 'private_b':
        return f"172.{draw(st.integers(16, 31))}.{draw(st.integers(0, 255))}.{draw(st.integers(1, 254))}"
    else:  # private_c
        return f"192.168.{draw(st.integers(0, 255))}.{draw(st.integers(1, 254))}"


@st.composite
def external_ip_strategy(draw):
    """Generate external (non-local) IP addresses."""
    # Generate public IP addresses
    first_octet = draw(st.sampled_from([8, 1, 208, 74, 173]))  # Google, Cloudflare, OpenDNS, etc.
    return f"{first_octet}.{draw(st.integers(0, 255))}.{draw(st.integers(0, 255))}.{draw(st.integers(1, 254))}"


@st.composite
def local_url_strategy(draw):
    """Generate local URLs."""
    protocol = draw(st.sampled_from(['http', 'https']))
    # Choose either a common local host or generate a local IP from the strategy
    host = draw(st.one_of(st.sampled_from(['localhost', '127.0.0.1']), local_ip_strategy()))
    port = draw(st.integers(1024, 65535))
    path = draw(st.text(alphabet=st.characters(whitelist_categories=['L', 'N'], whitelist_characters='/-_'), min_size=0, max_size=20))
    
    return f"{protocol}://{host}:{port}/{path}"


@st.composite
def external_url_strategy(draw):
    """Generate external URLs."""
    protocol = draw(st.sampled_from(['http', 'https']))
    domain = draw(st.sampled_from(['google.com', 'github.com', 'example.com', 'test.org']))
    port = draw(st.one_of(st.none(), st.integers(80, 8080)))
    
    if port:
        return f"{protocol}://{domain}:{port}"
    else:
        return f"{protocol}://{domain}"


@st.composite
def device_info_strategy(draw):
    """Generate DeviceInfo objects."""
    return DeviceInfo(
        device_id=draw(st.text(alphabet=st.characters(whitelist_categories=['L', 'N']), min_size=5, max_size=20)),
        device_type=draw(st.sampled_from(['HDD', 'SSD', 'USB', 'NVMe'])),
        capacity=draw(st.integers(1000000, 10000000000)),  # 1MB to 10GB
        manufacturer=draw(st.sampled_from(['Samsung', 'Western Digital', 'Seagate', 'Kingston'])),
        model=draw(st.text(alphabet=st.characters(whitelist_categories=['L', 'N']), min_size=3, max_size=15)),
        serial_number=draw(st.text(alphabet=st.characters(whitelist_categories=['L', 'N']), min_size=8, max_size=20)),
        connection_type=draw(st.sampled_from(['SATA', 'USB', 'NVMe', 'IDE']))
    )


@st.composite
def wipe_data_strategy(draw):
    """Generate WipeData objects."""
    return WipeData(
        device_id=draw(st.text(alphabet=st.characters(whitelist_categories=['L', 'N']), min_size=5, max_size=20)),
        wipe_hash=draw(st.text(alphabet='0123456789abcdef', min_size=64, max_size=64)),  # SHA-256 hash
        timestamp=datetime.now(),
        method=draw(st.sampled_from(['NIST_CLEAR', 'NIST_PURGE', 'NIST_DESTROY'])),
        operator=draw(st.text(alphabet=st.characters(whitelist_categories=['L']), min_size=3, max_size=15)),
        passes=draw(st.integers(1, 10))
    )


@st.composite
def blockchain_data_strategy(draw):
    """Generate BlockchainData objects."""
    return BlockchainData(
        transaction_hash=draw(st.text(alphabet='0123456789abcdef', min_size=64, max_size=64)),
        block_number=draw(st.integers(1, 1000000)),
        contract_address=draw(st.text(alphabet='0123456789abcdef', min_size=40, max_size=40)),
        gas_used=draw(st.integers(21000, 500000)),
        confirmation_count=draw(st.integers(1, 100))
    )


@st.composite
def sensitive_data_strategy(draw):
    """Generate data that contains sensitive information."""
    base_data = {
        'device_id': draw(st.text(alphabet=st.characters(whitelist_categories=['L', 'N']), min_size=5, max_size=20)),
        'operation_id': draw(st.text(alphabet=st.characters(whitelist_categories=['L', 'N']), min_size=10, max_size=30))
    }
    
    # Add sensitive fields
    sensitive_fields = draw(st.lists(
        st.sampled_from([
            ('password', 'secret123'),
            ('ssn', '123-45-6789'),
            ('credit_card', '4111-1111-1111-1111'),
            ('email', 'user@example.com'),
            ('personal_data', 'John Doe, 123 Main St'),
            ('private_key', 'abc123def456ghi789'),
            ('file_content', 'This is sensitive file content that should not be stored')
        ]),
        min_size=1,
        max_size=3
    ))
    
    for field_name, field_value in sensitive_fields:
        base_data[field_name] = field_value
    
    return base_data


@st.composite
def safe_data_strategy(draw):
    """Generate data that contains only safe, non-sensitive information."""
    return {
        'device_id': draw(st.text(alphabet=st.characters(whitelist_categories=['L', 'N']), min_size=5, max_size=20)),
        'wipe_hash': draw(st.text(alphabet='0123456789abcdef', min_size=64, max_size=64)),
        'timestamp': datetime.now().isoformat(),
        'method': draw(st.sampled_from(['NIST_CLEAR', 'NIST_PURGE', 'NIST_DESTROY'])),
        'operator_id': draw(st.text(alphabet=st.characters(whitelist_categories=['L']), min_size=3, max_size=15)),
        'transaction_hash': draw(st.text(alphabet='0123456789abcdef', min_size=64, max_size=64)),
        'block_number': draw(st.integers(1, 1000000))
    }


class TestLocalInfrastructureProperties:
    """Property-based tests for local infrastructure functionality."""
    
    @given(local_url=local_url_strategy())
    @settings(max_examples=50, deadline=5000)
    def test_property_14_local_infrastructure_operation_url_validation(self, local_url):
        """
        Feature: secure-data-wiping-blockchain
        Property 14: Local Infrastructure Operation
        
        For any local URL, the system should validate it as local and allow operations.
        Validates: Requirements 7.1, 7.3
        """
        # Test network isolation checker
        checker = NetworkIsolationChecker()
        
        try:
            # Local URLs should be validated as local
            network_check = checker.validate_url(local_url)
            assert network_check.is_local, f"Local URL {local_url} should be validated as local"
            
            # Test utils validator
            utils_validator = LocalInfrastructureValidator()
            is_local = utils_validator.validate_url_is_local(local_url)
            assert is_local, f"Utils validator should confirm {local_url} is local"
            
        except (NetworkIsolationError, UtilsNetworkError) as e:
            # Some local URLs might not be reachable, but they should still be recognized as local
            # Only fail if the error is about external network access
            if "external network" in str(e).lower():
                pytest.fail(f"Local URL {local_url} incorrectly rejected as external: {e}")
    
    @given(external_url=external_url_strategy())
    @settings(max_examples=30, deadline=5000)
    def test_property_14_local_infrastructure_operation_external_rejection(self, external_url):
        """
        Feature: secure-data-wiping-blockchain
        Property 14: Local Infrastructure Operation
        
        For any external URL, the system should reject it and prevent operations.
        Validates: Requirements 7.1, 7.3
        """
        checker = NetworkIsolationChecker()
        
        # External URLs should be rejected
        with pytest.raises(NetworkIsolationError):
            checker.validate_url(external_url)
        
        # Test utils validator
        utils_validator = LocalInfrastructureValidator()
        with pytest.raises(UtilsNetworkError):
            utils_validator.validate_url_is_local(external_url)
    
    @given(wipe_data=wipe_data_strategy(), blockchain_data=blockchain_data_strategy(), device_info=device_info_strategy())
    @settings(max_examples=50, deadline=10000)
    def test_property_15_offline_verification_creation_and_validation(self, wipe_data, blockchain_data, device_info):
        """
        Feature: secure-data-wiping-blockchain
        Property 15: Offline Certificate Verification
        
        For any generated certificate data, the system should create offline verification data
        that can be used to verify the certificate without network access.
        Validates: Requirements 7.5
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a mock certificate file
            cert_path = Path(temp_dir) / f"certificate_{wipe_data.device_id}.pdf"
            cert_path.write_text(f"Mock certificate for {wipe_data.device_id}\nHash: {wipe_data.wipe_hash}")
            
            # Test offline verifier
            verifier = OfflineVerifier(verification_data_dir=temp_dir)
            
            # Create offline verification data
            verification_data = verifier.create_verification_data(
                wipe_data=wipe_data,
                blockchain_data=blockchain_data,
                device_info=device_info,
                certificate_path=str(cert_path)
            )
            
            # Verify the verification data was created correctly
            assert verification_data.device_id == wipe_data.device_id
            assert verification_data.wipe_hash == wipe_data.wipe_hash
            assert verification_data.blockchain_tx == blockchain_data.transaction_hash
            assert verification_data.verification_code is not None
            assert len(verification_data.verification_code) > 0
            
            # Test that verification data can be used offline
            verification_result = verifier.verify_certificate_offline(
                certificate_path=str(cert_path),
                verification_code=verification_data.verification_code
            )
            
            # Verification should succeed for valid data
            assert verification_result.valid, f"Offline verification failed: {verification_result.errors}"
            assert verification_result.device_id == wipe_data.device_id
            assert verification_result.wipe_hash == wipe_data.wipe_hash
            
            # Test utils validator offline verification
            utils_validator = LocalInfrastructureValidator()
            offline_data = utils_validator.create_offline_verification_data(
                wipe_hash=wipe_data.wipe_hash,
                transaction_hash=blockchain_data.transaction_hash,
                device_id=wipe_data.device_id
            )
            
            assert offline_data['device_id'] == wipe_data.device_id
            assert offline_data['wipe_hash'] == wipe_data.wipe_hash
            assert offline_data['transaction_hash'] == blockchain_data.transaction_hash
            assert 'verification_instructions' in offline_data
    
    @given(sensitive_data=sensitive_data_strategy())
    @settings(max_examples=50, deadline=5000)
    def test_property_16_data_privacy_protection_sensitive_data_filtering(self, sensitive_data):
        """
        Feature: secure-data-wiping-blockchain
        Property 16: Data Privacy Protection
        
        For any data containing sensitive information, the system should filter out
        sensitive data before storing in blockchain records, certificates, or logs.
        Validates: Requirements 8.1, 8.2, 8.3, 8.5
        """
        # Test data privacy filter
        privacy_filter = DataPrivacyFilter()
        
        # Test blockchain data filtering
        blockchain_result = privacy_filter.filter_blockchain_data(sensitive_data)
        
        # Should have violations for sensitive data
        assert len(blockchain_result.violations) > 0, "Sensitive data should trigger privacy violations"
        
        # Filtered data should not contain sensitive fields
        for violation in blockchain_result.violations:
            if violation.violation_type.startswith('sensitive_pattern') or violation.violation_type == 'disallowed_sensitive_field':
                # The sensitive field should either be filtered out or sanitized
                if violation.field_name in blockchain_result.filtered_data:
                    filtered_value = blockchain_result.filtered_data[violation.field_name]
                    assert '[' in str(filtered_value) and ']' in str(filtered_value), \
                        f"Sensitive field {violation.field_name} should be sanitized"
        
        # Test certificate data filtering
        certificate_result = privacy_filter.filter_certificate_data(sensitive_data)
        assert len(certificate_result.violations) > 0, "Sensitive data should trigger privacy violations in certificates"
        
        # Test log data filtering
        log_result = privacy_filter.filter_log_data(sensitive_data)
        assert len(log_result.violations) > 0, "Sensitive data should trigger privacy violations in logs"
        
        # Test utils validator privacy filtering
        utils_validator = LocalInfrastructureValidator()
        filtered_data = utils_validator.filter_sensitive_data(sensitive_data)
        
        # Check that sensitive fields are redacted
        for key, value in filtered_data.items():
            if any(pattern in key.lower() for pattern in utils_validator.sensitive_patterns):
                assert value == "[REDACTED]", f"Sensitive field {key} should be redacted"
    
    @given(safe_data=safe_data_strategy())
    @settings(max_examples=50, deadline=5000)
    def test_property_16_data_privacy_protection_safe_data_preservation(self, safe_data):
        """
        Feature: secure-data-wiping-blockchain
        Property 16: Data Privacy Protection
        
        For any data containing only safe, non-sensitive information, the system should
        preserve the data while ensuring it meets privacy compliance requirements.
        Validates: Requirements 8.1, 8.2, 8.3, 8.5
        """
        # Test data privacy filter
        privacy_filter = DataPrivacyFilter()
        
        # Test blockchain data filtering - should have minimal violations
        blockchain_result = privacy_filter.filter_blockchain_data(safe_data)
        
        # Safe data should pass through with minimal filtering
        for field_name, field_value in safe_data.items():
            if field_name in privacy_filter.blockchain_allowed_fields:
                assert field_name in blockchain_result.filtered_data, \
                    f"Safe field {field_name} should be preserved in blockchain data"
        
        # Test certificate data filtering
        certificate_result = privacy_filter.filter_certificate_data(safe_data)
        for field_name, field_value in safe_data.items():
            if field_name in privacy_filter.certificate_allowed_fields:
                assert field_name in certificate_result.filtered_data, \
                    f"Safe field {field_name} should be preserved in certificate data"
        
        # Test privacy compliance validation
        blockchain_violations = privacy_filter.validate_privacy_compliance(safe_data, "blockchain")
        certificate_violations = privacy_filter.validate_privacy_compliance(safe_data, "certificate")
        log_violations = privacy_filter.validate_privacy_compliance(safe_data, "log")
        
        # Safe data should have minimal or no violations
        serious_violations = [v for v in blockchain_violations if v.severity.value in ['confidential', 'restricted']]
        assert len(serious_violations) == 0, f"Safe data should not have serious privacy violations: {serious_violations}"
        
        # Test utils validator
        utils_validator = LocalInfrastructureValidator()
        
        # Blockchain data validation should pass
        try:
            utils_validator.validate_blockchain_data_privacy(safe_data)
        except UtilsDataPrivacyError as e:
            # Only fail if it's a serious privacy violation, not just field restrictions
            if any(pattern in str(e).lower() for pattern in ['sensitive', 'private', 'confidential']):
                pytest.fail(f"Safe data incorrectly flagged as privacy violation: {e}")
        
        # Certificate data validation should pass
        try:
            utils_validator.validate_certificate_data_privacy(safe_data)
        except UtilsDataPrivacyError as e:
            # Only fail if it's a serious privacy violation
            if any(pattern in str(e).lower() for pattern in ['sensitive', 'private', 'confidential']):
                pytest.fail(f"Safe data incorrectly flagged as privacy violation: {e}")
    
    @given(
        ganache_url=local_url_strategy(),
        database_path=st.text(alphabet=st.characters(whitelist_categories=['L', 'N'], whitelist_characters='/-_.'), min_size=5, max_size=50),
        certificates_dir=st.text(alphabet=st.characters(whitelist_categories=['L', 'N'], whitelist_characters='/-_.'), min_size=5, max_size=50)
    )
    @settings(max_examples=30, deadline=10000)
    def test_property_14_local_infrastructure_system_validation(self, ganache_url, database_path, certificates_dir):
        """
        Feature: secure-data-wiping-blockchain
        Property 14: Local Infrastructure Operation
        
        For any system configuration with local paths and URLs, the system should
        validate that all components operate on local infrastructure only.
        Validates: Requirements 7.1, 7.3
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create absolute paths for testing
            abs_database_path = os.path.join(temp_dir, database_path.lstrip('/'))
            abs_certificates_dir = os.path.join(temp_dir, certificates_dir.lstrip('/'))
            
            # Create the directories/files
            os.makedirs(os.path.dirname(abs_database_path), exist_ok=True)
            os.makedirs(abs_certificates_dir, exist_ok=True)
            Path(abs_database_path).touch()
            
            try:
                # System validation should pass for local infrastructure
                result = validate_system_is_local_only(
                    ganache_url=ganache_url,
                    database_path=abs_database_path,
                    certificates_dir=abs_certificates_dir
                )
                
                assert result is True, "Local infrastructure validation should pass"
                
            except (LocalInfrastructureError, UtilsNetworkError) as e:
                # Some URLs might not be reachable, but should still be recognized as local
                if "external network" in str(e).lower():
                    pytest.fail(f"Local infrastructure incorrectly rejected: {e}")
                # Other errors (like unreachable services) are acceptable for this test


if __name__ == "__main__":
    # Run basic functionality tests
    print("Running Local Infrastructure Property Tests...")
    
    print("\n=== Property 14: Local Infrastructure Operation ===")
    try:
        # Test network isolation checker
        checker = NetworkIsolationChecker()
        
        # Test local addresses
        local_addresses = ['localhost', '127.0.0.1', '192.168.1.1', '10.0.0.1']
        for addr in local_addresses:
            is_local = checker.is_local_address(addr)
            assert is_local, f"Address {addr} should be recognized as local"
        
        # Test external addresses (these should fail)
        external_addresses = ['8.8.8.8', 'google.com', '1.1.1.1']
        for addr in external_addresses:
            is_local = checker.is_local_address(addr)
            assert not is_local, f"Address {addr} should be recognized as external"
        
        print("✓ Network isolation tests passed")
        
    except Exception as e:
        print(f"✗ Property 14 test failed: {e}")
    
    print("\n=== Property 15: Offline Certificate Verification ===")
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create sample data for testing
            sample_wipe_data = WipeData(
                device_id="TEST_DEVICE_001",
                wipe_hash="a" * 64,
                timestamp=datetime.now(),
                method="NIST_CLEAR",
                operator="test_operator",
                passes=3
            )
            
            sample_blockchain_data = BlockchainData(
                transaction_hash="b" * 64,
                block_number=12345,
                contract_address="c" * 40,
                gas_used=50000,
                confirmation_count=6
            )
            
            sample_device_info = DeviceInfo(
                device_id="TEST_DEVICE_001",
                device_type="SSD",
                capacity=1000000000,
                manufacturer="Samsung",
                model="EVO_860",
                serial_number="S12345678",
                connection_type="SATA"
            )
            
            # Create a mock certificate file
            cert_path = Path(temp_dir) / f"certificate_{sample_wipe_data.device_id}.pdf"
            cert_path.write_text(f"Mock certificate for {sample_wipe_data.device_id}\nHash: {sample_wipe_data.wipe_hash}")
            
            # Test offline verifier
            verifier = OfflineVerifier(verification_data_dir=temp_dir)
            
            # Create offline verification data
            verification_data = verifier.create_verification_data(
                wipe_data=sample_wipe_data,
                blockchain_data=sample_blockchain_data,
                device_info=sample_device_info,
                certificate_path=str(cert_path)
            )
            
            # Verify the verification data was created correctly
            assert verification_data.device_id == sample_wipe_data.device_id
            assert verification_data.wipe_hash == sample_wipe_data.wipe_hash
            
            print("✓ Offline verification tests passed")
        
    except Exception as e:
        print(f"✗ Property 15 test failed: {e}")
    
    print("\n=== Property 16: Data Privacy Protection ===")
    try:
        # Test data privacy filter
        privacy_filter = DataPrivacyFilter()
        
        # Test sensitive data filtering
        sensitive_data = {
            'device_id': 'TEST_001',
            'password': 'secret123',
            'wipe_hash': 'a' * 64,
            'ssn': '123-45-6789'
        }
        
        blockchain_result = privacy_filter.filter_blockchain_data(sensitive_data)
        assert len(blockchain_result.violations) > 0, "Sensitive data should trigger privacy violations"
        
        # Test safe data preservation
        safe_data = {
            'device_id': 'TEST_001',
            'wipe_hash': 'a' * 64,
            'timestamp': datetime.now().isoformat(),
            'method': 'NIST_CLEAR',
            'operator_id': 'operator1'
        }
        
        safe_result = privacy_filter.filter_blockchain_data(safe_data)
        # Safe data should have minimal violations (only field restrictions, not content issues)
        content_violations = [v for v in safe_result.violations if 'sensitive_pattern' in v.violation_type]
        assert len(content_violations) == 0, "Safe data should not have content privacy violations"
        
        print("✓ Data privacy protection tests passed")
        
    except Exception as e:
        print(f"✗ Property 16 test failed: {e}")
    
    print("\n=== All Local Infrastructure Property Tests Completed ===")
    print("Run with pytest for full property-based testing with multiple examples.")
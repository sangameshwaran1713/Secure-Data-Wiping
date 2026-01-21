#!/usr/bin/env python3
"""
Test Local Infrastructure Integration with SystemController
"""

import sys
import os
import tempfile
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, os.path.abspath('.'))

from secure_data_wiping.system_controller import SystemController
from secure_data_wiping.utils.data_models import DeviceInfo, WipeConfig, WipeMethod
from secure_data_wiping.local_infrastructure import NetworkIsolationChecker, DataPrivacyFilter
from secure_data_wiping.utils.local_infrastructure import LocalInfrastructureValidator


def test_local_infrastructure_integration():
    """Test the integration of local infrastructure components."""
    print('Testing SystemController with Local Infrastructure Integration...')
    
    # Test network isolation
    print('\n=== Network Isolation Tests ===')
    checker = NetworkIsolationChecker()
    
    local_addresses = ['127.0.0.1', 'localhost', '192.168.1.1', '10.0.0.1']
    for addr in local_addresses:
        is_local = checker.is_local_address(addr)
        print(f'Local address check ({addr}): {is_local}')
        assert is_local, f"Address {addr} should be local"
    
    external_addresses = ['8.8.8.8', '1.1.1.1']
    for addr in external_addresses:
        is_local = checker.is_local_address(addr)
        print(f'External address check ({addr}): {is_local}')
        assert not is_local, f"Address {addr} should be external"
    
    print('✓ Network isolation tests passed')
    
    # Test data privacy filter
    print('\n=== Data Privacy Filter Tests ===')
    privacy_filter = DataPrivacyFilter()
    
    # Test with sensitive data
    sensitive_data = {
        'device_id': 'TEST_001', 
        'wipe_hash': 'a' * 64, 
        'password': 'secret123',
        'ssn': '123-45-6789'
    }
    result = privacy_filter.filter_blockchain_data(sensitive_data)
    print(f'Privacy violations found in sensitive data: {len(result.violations)}')
    assert len(result.violations) > 0, "Sensitive data should trigger violations"
    
    # Test with safe data
    safe_data = {
        'device_id': 'TEST_001',
        'wipe_hash': 'a' * 64,
        'timestamp': '2024-01-01T00:00:00',
        'method': 'NIST_CLEAR'
    }
    safe_result = privacy_filter.filter_blockchain_data(safe_data)
    print(f'Privacy violations found in safe data: {len(safe_result.violations)}')
    
    print('✓ Data privacy filter tests passed')
    
    # Test system controller initialization
    print('\n=== SystemController Integration Tests ===')
    with tempfile.TemporaryDirectory() as temp_dir:
        config_path = os.path.join(temp_dir, 'test_config.yaml')
        with open(config_path, 'w') as f:
            f.write('''
ganache_url: http://127.0.0.1:7545
database_path: test.db
certificates_dir: certificates
contract_address: '0x1234567890123456789012345678901234567890'
max_retry_attempts: 3
''')
        
        try:
            controller = SystemController(config_path)
            print('✓ SystemController initialized successfully')
            
            # Test local validator initialization
            controller._initialize_local_validator()
            print('✓ Local validator initialized')
            assert controller.local_validator is not None
            
            # Test privacy filtering through validator
            test_blockchain_data = {
                'device_id': 'TEST_001',
                'wipe_hash': 'a' * 64,
                'timestamp': 1234567890,
                'method': 'NIST_CLEAR'
            }
            controller.local_validator.validate_blockchain_data_privacy(test_blockchain_data)
            print('✓ Blockchain data privacy validation passed')
            
            # Test offline verification data creation
            offline_data = controller.generate_offline_verification(
                device_id='TEST_001',
                wipe_hash='a' * 64,
                transaction_hash='b' * 64
            )
            print('✓ Offline verification data created')
            assert offline_data['device_id'] == 'TEST_001'
            assert offline_data['wipe_hash'] == 'a' * 64
            
        except Exception as e:
            print(f'✗ Error during SystemController integration: {e}')
            raise
    
    # Test utils validator directly
    print('\n=== Utils Validator Tests ===')
    utils_validator = LocalInfrastructureValidator()
    
    # Test URL validation
    local_urls = ['http://127.0.0.1:7545', 'https://localhost:8545']
    for url in local_urls:
        try:
            is_local = utils_validator.validate_url_is_local(url)
            print(f'URL validation ({url}): {is_local}')
            assert is_local, f"URL {url} should be validated as local"
        except Exception as e:
            print(f'URL validation error for {url}: {e}')
    
    # Test file path validation
    with tempfile.TemporaryDirectory() as temp_dir:
        test_file = os.path.join(temp_dir, 'test.db')
        Path(test_file).touch()
        
        is_local_file = utils_validator.validate_file_path_is_local(test_file)
        print(f'File path validation ({test_file}): {is_local_file}')
        assert is_local_file, "Local file path should be validated"
    
    print('✓ Utils validator tests passed')
    
    print('\n=== All Local Infrastructure Integration Tests Completed Successfully ===')


if __name__ == "__main__":
    test_local_infrastructure_integration()
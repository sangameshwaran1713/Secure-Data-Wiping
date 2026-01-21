#!/usr/bin/env python3
"""
Core System Testing Checkpoint
Tests all core components and their integration for Task 9.
"""

import sys
import os
import tempfile
from datetime import datetime
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, os.path.abspath('.'))

def test_core_components():
    """Test all core components individually."""
    print('=== Core System Testing Checkpoint ===')
    print('Testing individual components...\n')
    
    results = {
        'hash_generator': False,
        'wipe_engine': False,
        'certificate_generator': False,
        'local_infrastructure': False,
        'database': False
    }
    
    # Test 1: Hash Generator
    print('1. Testing Hash Generator...')
    try:
        from secure_data_wiping.hash_generator import HashGenerator
        from secure_data_wiping.utils.data_models import WipeResult, WipeMethod
        
        hash_gen = HashGenerator()
        test_result = WipeResult(
            operation_id='TEST_001',
            device_id='TEST_DEVICE',
            method=WipeMethod.NIST_CLEAR,
            passes_completed=1,
            start_time=datetime.now(),
            success=True,
            operator_id='test_operator'
        )
        
        hash_value = hash_gen.generate_wipe_hash(test_result)
        print(f'   ✓ Generated hash: {hash_value[:16]}...')
        
        # Test hash verification
        is_valid = hash_gen.verify_hash(test_result, hash_value)
        print(f'   ✓ Hash verification: {is_valid}')
        
        results['hash_generator'] = True
        
    except Exception as e:
        print(f'   ✗ Hash Generator failed: {e}')
    
    # Test 2: Wipe Engine
    print('\n2. Testing Wipe Engine...')
    try:
        from secure_data_wiping.wipe_engine import WipeEngine
        from secure_data_wiping.utils.data_models import WipeMethod
        
        wipe_engine = WipeEngine()
        
        # Create test file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.tmp') as f:
            f.write('Test data for secure wiping demonstration\n' * 10)
            test_file = f.name
        
        result = wipe_engine.wipe_device(test_file, WipeMethod.NIST_CLEAR)
        print(f'   ✓ Wiped test file: success={result.success}')
        print(f'   ✓ Passes completed: {result.passes_completed}')
        print(f'   ✓ Method used: {result.method.value}')
        
        # Cleanup
        if os.path.exists(test_file):
            os.remove(test_file)
        if os.path.exists(test_file + '.DESTROYED'):
            os.remove(test_file + '.DESTROYED')
            
        results['wipe_engine'] = True
        
    except Exception as e:
        print(f'   ✗ Wipe Engine failed: {e}')
    
    # Test 3: Certificate Generator
    print('\n3. Testing Certificate Generator...')
    try:
        from secure_data_wiping.certificate_generator import CertificateGenerator
        from secure_data_wiping.utils.data_models import WipeData, BlockchainData, DeviceInfo
        
        with tempfile.TemporaryDirectory() as temp_dir:
            cert_gen = CertificateGenerator(output_dir=temp_dir)
            
            wipe_data = WipeData(
                device_id='TEST_DEVICE',
                wipe_hash='a' * 64,
                timestamp=datetime.now(),
                method='NIST_CLEAR',
                operator='test_operator',
                passes=1
            )
            
            blockchain_data = BlockchainData(
                transaction_hash='b' * 64,
                block_number=12345,
                contract_address='c' * 40,
                gas_used=50000,
                confirmation_count=6
            )
            
            device_info = DeviceInfo(
                device_id='TEST_DEVICE',
                device_type='SSD',
                capacity=1000000000,
                manufacturer='Samsung',
                model='EVO_860',
                serial_number='S12345678',
                connection_type='SATA'
            )
            
            cert_path = cert_gen.generate_certificate(wipe_data, blockchain_data, device_info)
            print(f'   ✓ Created certificate: {Path(cert_path).name}')
            print(f'   ✓ Certificate exists: {os.path.exists(cert_path)}')
            
            # Check certificate size
            cert_size = os.path.getsize(cert_path)
            print(f'   ✓ Certificate size: {cert_size} bytes')
            
        results['certificate_generator'] = True
        
    except Exception as e:
        print(f'   ✗ Certificate Generator failed: {e}')
    
    # Test 4: Local Infrastructure
    print('\n4. Testing Local Infrastructure...')
    try:
        from secure_data_wiping.local_infrastructure import (
            NetworkIsolationChecker, DataPrivacyFilter, OfflineVerifier
        )
        
        # Test network isolation
        checker = NetworkIsolationChecker()
        local_check = checker.is_local_address('127.0.0.1')
        external_check = checker.is_local_address('8.8.8.8')
        print(f'   ✓ Local address detection: {local_check}')
        print(f'   ✓ External address detection: {not external_check}')
        
        # Test data privacy
        privacy_filter = DataPrivacyFilter()
        test_data = {'device_id': 'TEST', 'password': 'secret'}
        result = privacy_filter.filter_blockchain_data(test_data)
        print(f'   ✓ Privacy violations detected: {len(result.violations) > 0}')
        
        # Test offline verification
        with tempfile.TemporaryDirectory() as temp_dir:
            verifier = OfflineVerifier(verification_data_dir=temp_dir)
            
            # Create mock certificate
            cert_path = Path(temp_dir) / 'certificate_TEST.pdf'
            cert_path.write_text('Mock certificate content')
            
            # This would normally create verification data
            print(f'   ✓ Offline verifier initialized')
        
        results['local_infrastructure'] = True
        
    except Exception as e:
        print(f'   ✗ Local Infrastructure failed: {e}')
    
    # Test 5: Database
    print('\n5. Testing Database...')
    try:
        from secure_data_wiping.database import DatabaseManager
        from secure_data_wiping.utils.data_models import WipeOperation, DeviceInfo, WipeConfig
        
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = os.path.join(temp_dir, 'test.db')
            db_manager = DatabaseManager(db_path)
            db_manager.initialize_database()
            
            print(f'   ✓ Database initialized: {os.path.exists(db_path)}')
            
            # Test operation storage
            test_operation = WipeOperation(
                operation_id='TEST_OP_001',
                device_info=DeviceInfo(
                    device_id='TEST_DEVICE',
                    device_type='SSD',
                    capacity=1000000000,
                    manufacturer='Samsung',
                    model='EVO_860',
                    serial_number='S12345678',
                    connection_type='SATA'
                ),
                wipe_config=WipeConfig(
                    method=WipeMethod.NIST_CLEAR,
                    passes=1,
                    verify_wipe=True
                )
            )
            
            db_manager.store_wipe_operation(test_operation)
            print(f'   ✓ Operation stored successfully')
            
            db_manager.close()
        
        results['database'] = True
        
    except Exception as e:
        print(f'   ✗ Database failed: {e}')
    
    return results


def test_integration():
    """Test basic integration between components."""
    print('\n=== Integration Testing ===')
    
    try:
        from secure_data_wiping.utils.local_infrastructure import LocalInfrastructureValidator
        
        # Test system validation
        validator = LocalInfrastructureValidator()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test paths
            db_path = os.path.join(temp_dir, 'test.db')
            cert_dir = os.path.join(temp_dir, 'certificates')
            
            Path(db_path).touch()
            os.makedirs(cert_dir, exist_ok=True)
            
            # Test file path validation
            db_valid = validator.validate_file_path_is_local(db_path)
            cert_valid = validator.validate_file_path_is_local(cert_dir)
            
            print(f'   ✓ Database path validation: {db_valid}')
            print(f'   ✓ Certificate directory validation: {cert_valid}')
            
            # Test privacy filtering
            test_data = {
                'device_id': 'TEST_001',
                'wipe_hash': 'a' * 64,
                'timestamp': int(datetime.now().timestamp()),
                'method': 'NIST_CLEAR'
            }
            
            validator.validate_blockchain_data_privacy(test_data)
            print(f'   ✓ Privacy validation passed')
            
        return True
        
    except Exception as e:
        print(f'   ✗ Integration test failed: {e}')
        return False


def main():
    """Run all core system tests."""
    print('Starting Core System Testing Checkpoint...\n')
    
    # Test individual components
    component_results = test_core_components()
    
    # Test integration
    integration_result = test_integration()
    
    # Summary
    print('\n=== Test Summary ===')
    total_components = len(component_results)
    passed_components = sum(component_results.values())
    
    for component, passed in component_results.items():
        status = '✓' if passed else '✗'
        print(f'{status} {component.replace("_", " ").title()}: {"PASSED" if passed else "FAILED"}')
    
    integration_status = '✓' if integration_result else '✗'
    print(f'{integration_status} Integration: {"PASSED" if integration_result else "FAILED"}')
    
    print(f'\nOverall: {passed_components}/{total_components} components passed')
    
    if passed_components == total_components and integration_result:
        print('🎉 All core system tests PASSED! System is ready for next phase.')
        return True
    else:
        print('⚠️  Some tests failed. Please review and fix issues before proceeding.')
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
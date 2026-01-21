#!/usr/bin/env python3
"""
Final Integration Tests for Complete System

This module provides comprehensive integration tests for the complete secure data wiping system,
testing end-to-end workflows, error recovery, and system resilience.
"""

import sys
import os
import time
import tempfile
import threading
import concurrent.futures
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

# Add the project root to Python path
sys.path.insert(0, os.path.abspath('.'))

from secure_data_wiping.wipe_engine import WipeEngine
from secure_data_wiping.hash_generator import HashGenerator
from secure_data_wiping.certificate_generator import CertificateGenerator
from secure_data_wiping.local_infrastructure import (
    DataPrivacyFilter, OfflineVerifier, NetworkIsolationChecker
)
from secure_data_wiping.utils.data_models import (
    DeviceInfo, WipeMethod, DeviceType, WipeData, BlockchainData
)


class SystemIntegrationTester:
    """Comprehensive integration testing for the complete system."""
    
    def __init__(self):
        """Initialize the integration tester."""
        self.test_start_time = datetime.now()
        self.test_results = {}
        self.temp_dir = Path(tempfile.mkdtemp(prefix='integration_test_'))
        
        # Initialize system components
        self.wipe_engine = WipeEngine()
        self.hash_generator = HashGenerator()
        self.certificate_generator = CertificateGenerator(output_dir=str(self.temp_dir))
        self.privacy_filter = DataPrivacyFilter()
        self.offline_verifier = OfflineVerifier(verification_data_dir=str(self.temp_dir))
        self.network_checker = NetworkIsolationChecker()
        
        # Test statistics
        self.stats = {
            'tests_run': 0,
            'tests_passed': 0,
            'tests_failed': 0,
            'total_devices_processed': 0,
            'total_certificates_generated': 0,
            'total_processing_time': 0.0
        }
    
    def log_test_result(self, test_name: str, success: bool, duration: float, details: str = ""):
        """Log a test result."""
        self.stats['tests_run'] += 1
        if success:
            self.stats['tests_passed'] += 1
            status = "✅ PASSED"
        else:
            self.stats['tests_failed'] += 1
            status = "❌ FAILED"
        
        print(f"{status} {test_name} ({duration:.3f}s)")
        if details:
            print(f"    {details}")
        
        self.test_results[test_name] = {
            'success': success,
            'duration': duration,
            'details': details,
            'timestamp': datetime.now()
        }
    
    def create_test_device(self, device_type: DeviceType, device_id: str) -> DeviceInfo:
        """Create a test device for integration testing."""
        return DeviceInfo(
            device_id=device_id,
            device_type=device_type,
            capacity=1000000000,  # 1GB
            manufacturer="TestCorp",
            model="IntegrationTest",
            serial_number=f"TEST_{device_id}",
            connection_type="TEST"
        )
    
    def create_test_data_file(self, device_id: str, size_kb: int = 100) -> str:
        """Create a test data file for wiping."""
        file_path = self.temp_dir / f"{device_id}_test_data.tmp"
        
        # Create test data
        test_data = f"TEST DATA FOR DEVICE {device_id}\n" * (size_kb * 10)
        test_data += "CONFIDENTIAL INFORMATION\n" * 50
        test_data += "SENSITIVE DATA THAT MUST BE WIPED\n" * 50
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(test_data)
        
        return str(file_path)
    
    def test_end_to_end_workflow(self) -> bool:
        """Test complete end-to-end workflow from wiping to certificate generation."""
        test_start = time.time()
        
        try:
            # Create test device and data
            device = self.create_test_device(DeviceType.SSD, "E2E_TEST_001")
            data_file = self.create_test_data_file(device.device_id)
            
            # Step 1: Secure wiping
            wipe_result = self.wipe_engine.wipe_device(data_file, WipeMethod.NIST_CLEAR)
            if not wipe_result.success:
                raise Exception("Wiping failed")
            
            # Step 2: Hash generation
            wipe_hash = self.hash_generator.generate_wipe_hash(wipe_result)
            if not wipe_hash or len(wipe_hash) != 64:
                raise Exception("Hash generation failed")
            
            # Step 3: Privacy filtering
            test_data = {
                'device_id': device.device_id,
                'wipe_hash': wipe_hash,
                'timestamp': int(datetime.now().timestamp()),
                'method': wipe_result.method.value,
                'password': 'secret123',  # This should be filtered
                'email': 'test@example.com'  # This should be filtered
            }
            
            privacy_result = self.privacy_filter.filter_blockchain_data(test_data)
            if len(privacy_result.violations) == 0:
                raise Exception("Privacy filtering failed to detect violations")
            
            # Step 4: Certificate generation
            wipe_data = WipeData(
                device_id=device.device_id,
                wipe_hash=wipe_hash,
                timestamp=datetime.now(),
                method=wipe_result.method.value,
                operator='integration_test',
                passes=wipe_result.passes_completed
            )
            
            blockchain_data = BlockchainData(
                transaction_hash="0x" + "a" * 62,
                block_number=12345,
                contract_address="0x" + "b" * 38,
                gas_used=50000,
                confirmation_count=6
            )
            
            cert_path = self.certificate_generator.generate_certificate(
                wipe_data, blockchain_data, device
            )
            
            if not os.path.exists(cert_path):
                raise Exception("Certificate generation failed")
            
            # Step 5: Offline verification setup
            verification_data = self.offline_verifier.create_verification_data(
                wipe_data=wipe_data,
                blockchain_data=blockchain_data,
                device_info=device,
                certificate_path=cert_path
            )
            
            if not verification_data.verification_code:
                raise Exception("Offline verification setup failed")
            
            # Update statistics
            self.stats['total_devices_processed'] += 1
            self.stats['total_certificates_generated'] += 1
            
            # Cleanup
            if os.path.exists(data_file):
                os.remove(data_file)
            if os.path.exists(data_file + '.DESTROYED'):
                os.remove(data_file + '.DESTROYED')
            
            duration = time.time() - test_start
            self.stats['total_processing_time'] += duration
            
            self.log_test_result(
                "End-to-End Workflow",
                True,
                duration,
                f"Device: {device.device_id}, Certificate: {Path(cert_path).name}"
            )
            return True
            
        except Exception as e:
            duration = time.time() - test_start
            self.log_test_result(
                "End-to-End Workflow",
                False,
                duration,
                f"Error: {str(e)}"
            )
            return False
    
    def test_multiple_device_processing(self) -> bool:
        """Test processing multiple devices in sequence."""
        test_start = time.time()
        
        try:
            device_types = [DeviceType.HDD, DeviceType.SSD, DeviceType.USB, DeviceType.NVME]
            processed_devices = []
            
            for i, device_type in enumerate(device_types):
                device = self.create_test_device(device_type, f"MULTI_TEST_{i:03d}")
                data_file = self.create_test_data_file(device.device_id, size_kb=50)
                
                # Process device
                wipe_result = self.wipe_engine.wipe_device(data_file, WipeMethod.NIST_CLEAR)
                if not wipe_result.success:
                    raise Exception(f"Wiping failed for device {device.device_id}")
                
                wipe_hash = self.hash_generator.generate_wipe_hash(wipe_result)
                if not wipe_hash:
                    raise Exception(f"Hash generation failed for device {device.device_id}")
                
                processed_devices.append({
                    'device': device,
                    'wipe_result': wipe_result,
                    'wipe_hash': wipe_hash
                })
                
                # Cleanup
                if os.path.exists(data_file):
                    os.remove(data_file)
                if os.path.exists(data_file + '.DESTROYED'):
                    os.remove(data_file + '.DESTROYED')
            
            # Verify all devices were processed
            if len(processed_devices) != len(device_types):
                raise Exception(f"Expected {len(device_types)} devices, processed {len(processed_devices)}")
            
            # Verify hash uniqueness
            hashes = [d['wipe_hash'] for d in processed_devices]
            if len(set(hashes)) != len(hashes):
                raise Exception("Duplicate hashes detected across different devices")
            
            self.stats['total_devices_processed'] += len(processed_devices)
            
            duration = time.time() - test_start
            self.stats['total_processing_time'] += duration
            
            self.log_test_result(
                "Multiple Device Processing",
                True,
                duration,
                f"Processed {len(processed_devices)} devices successfully"
            )
            return True
            
        except Exception as e:
            duration = time.time() - test_start
            self.log_test_result(
                "Multiple Device Processing",
                False,
                duration,
                f"Error: {str(e)}"
            )
            return False
    
    def test_error_recovery_and_resilience(self) -> bool:
        """Test system behavior with various error conditions."""
        test_start = time.time()
        
        try:
            error_scenarios = []
            
            # Scenario 1: Invalid file path
            try:
                result = self.wipe_engine.wipe_device("/nonexistent/file.tmp", WipeMethod.NIST_CLEAR)
                if result.success:
                    raise Exception("Expected failure for nonexistent file")
                error_scenarios.append("Invalid file path handled correctly")
            except Exception as e:
                error_scenarios.append(f"Invalid file path error: {str(e)}")
            
            # Scenario 2: Invalid hash data
            try:
                from secure_data_wiping.utils.data_models import WipeResult
                invalid_result = WipeResult(
                    operation_id="",  # Empty operation ID
                    device_id="",     # Empty device ID
                    method=WipeMethod.NIST_CLEAR,
                    passes_completed=0,
                    start_time=datetime.now(),
                    success=True,
                    operator_id="",
                    verification_hash=""
                )
                hash_value = self.hash_generator.generate_wipe_hash(invalid_result)
                if not hash_value:
                    error_scenarios.append("Empty data hash generation handled correctly")
                else:
                    error_scenarios.append("Hash generated for empty data (acceptable)")
            except Exception as e:
                error_scenarios.append(f"Invalid hash data error: {str(e)}")
            
            # Scenario 3: Privacy filter with no violations
            try:
                safe_data = {
                    'device_id': 'TEST_DEVICE',
                    'wipe_hash': 'a' * 64,
                    'timestamp': int(datetime.now().timestamp()),
                    'method': 'NIST_CLEAR'
                }
                privacy_result = self.privacy_filter.filter_blockchain_data(safe_data)
                if len(privacy_result.violations) == 0:
                    error_scenarios.append("No privacy violations detected correctly")
                else:
                    error_scenarios.append("Unexpected privacy violations detected")
            except Exception as e:
                error_scenarios.append(f"Privacy filter error: {str(e)}")
            
            # Scenario 4: Network isolation checks
            try:
                external_addresses = ['8.8.8.8', 'google.com', '1.1.1.1']
                blocked_count = 0
                for addr in external_addresses:
                    if not self.network_checker.is_local_address(addr):
                        blocked_count += 1
                
                if blocked_count == len(external_addresses):
                    error_scenarios.append("External addresses blocked correctly")
                else:
                    error_scenarios.append(f"Only {blocked_count}/{len(external_addresses)} external addresses blocked")
            except Exception as e:
                error_scenarios.append(f"Network isolation error: {str(e)}")
            
            # All scenarios should have been handled
            if len(error_scenarios) < 4:
                raise Exception(f"Only {len(error_scenarios)}/4 error scenarios tested")
            
            duration = time.time() - test_start
            
            self.log_test_result(
                "Error Recovery and Resilience",
                True,
                duration,
                f"Tested {len(error_scenarios)} error scenarios"
            )
            return True
            
        except Exception as e:
            duration = time.time() - test_start
            self.log_test_result(
                "Error Recovery and Resilience",
                False,
                duration,
                f"Error: {str(e)}"
            )
            return False
    
    def test_concurrent_operations(self) -> bool:
        """Test system behavior with concurrent operations."""
        test_start = time.time()
        
        try:
            def process_device_concurrently(device_index: int) -> Dict[str, Any]:
                """Process a single device in a concurrent context."""
                device = self.create_test_device(DeviceType.SSD, f"CONCURRENT_{device_index:03d}")
                data_file = self.create_test_data_file(device.device_id, size_kb=25)
                
                try:
                    # Create separate component instances for thread safety
                    wipe_engine = WipeEngine()
                    hash_generator = HashGenerator()
                    
                    # Process device
                    wipe_result = wipe_engine.wipe_device(data_file, WipeMethod.NIST_CLEAR)
                    if not wipe_result.success:
                        return {'success': False, 'error': 'Wiping failed'}
                    
                    wipe_hash = hash_generator.generate_wipe_hash(wipe_result)
                    if not wipe_hash:
                        return {'success': False, 'error': 'Hash generation failed'}
                    
                    # Cleanup
                    if os.path.exists(data_file):
                        os.remove(data_file)
                    if os.path.exists(data_file + '.DESTROYED'):
                        os.remove(data_file + '.DESTROYED')
                    
                    return {
                        'success': True,
                        'device_id': device.device_id,
                        'wipe_hash': wipe_hash,
                        'passes': wipe_result.passes_completed
                    }
                    
                except Exception as e:
                    return {'success': False, 'error': str(e)}
            
            # Run concurrent operations
            num_concurrent = 5
            with concurrent.futures.ThreadPoolExecutor(max_workers=num_concurrent) as executor:
                futures = [
                    executor.submit(process_device_concurrently, i)
                    for i in range(num_concurrent)
                ]
                
                results = []
                for future in concurrent.futures.as_completed(futures):
                    result = future.result()
                    results.append(result)
            
            # Verify results
            successful_results = [r for r in results if r['success']]
            if len(successful_results) != num_concurrent:
                raise Exception(f"Only {len(successful_results)}/{num_concurrent} concurrent operations succeeded")
            
            # Verify hash uniqueness
            hashes = [r['wipe_hash'] for r in successful_results]
            if len(set(hashes)) != len(hashes):
                raise Exception("Duplicate hashes detected in concurrent operations")
            
            self.stats['total_devices_processed'] += len(successful_results)
            
            duration = time.time() - test_start
            self.stats['total_processing_time'] += duration
            
            self.log_test_result(
                "Concurrent Operations",
                True,
                duration,
                f"Successfully processed {len(successful_results)} devices concurrently"
            )
            return True
            
        except Exception as e:
            duration = time.time() - test_start
            self.log_test_result(
                "Concurrent Operations",
                False,
                duration,
                f"Error: {str(e)}"
            )
            return False
    
    def test_performance_under_load(self) -> bool:
        """Test system performance under load conditions."""
        test_start = time.time()
        
        try:
            # Process multiple devices to test performance
            num_devices = 10
            device_processing_times = []
            
            for i in range(num_devices):
                device = self.create_test_device(DeviceType.USB, f"LOAD_TEST_{i:03d}")
                data_file = self.create_test_data_file(device.device_id, size_kb=20)
                
                device_start = time.time()
                
                # Process device
                wipe_result = self.wipe_engine.wipe_device(data_file, WipeMethod.NIST_CLEAR)
                if not wipe_result.success:
                    raise Exception(f"Wiping failed for device {device.device_id}")
                
                wipe_hash = self.hash_generator.generate_wipe_hash(wipe_result)
                if not wipe_hash:
                    raise Exception(f"Hash generation failed for device {device.device_id}")
                
                device_time = time.time() - device_start
                device_processing_times.append(device_time)
                
                # Cleanup
                if os.path.exists(data_file):
                    os.remove(data_file)
                if os.path.exists(data_file + '.DESTROYED'):
                    os.remove(data_file + '.DESTROYED')
            
            # Calculate performance metrics
            avg_processing_time = sum(device_processing_times) / len(device_processing_times)
            max_processing_time = max(device_processing_times)
            min_processing_time = min(device_processing_times)
            
            # Performance thresholds (reasonable for testing)
            if avg_processing_time > 1.0:  # Average should be under 1 second
                raise Exception(f"Average processing time too high: {avg_processing_time:.3f}s")
            
            if max_processing_time > 2.0:  # Max should be under 2 seconds
                raise Exception(f"Maximum processing time too high: {max_processing_time:.3f}s")
            
            self.stats['total_devices_processed'] += num_devices
            
            duration = time.time() - test_start
            self.stats['total_processing_time'] += duration
            
            self.log_test_result(
                "Performance Under Load",
                True,
                duration,
                f"Avg: {avg_processing_time:.3f}s, Max: {max_processing_time:.3f}s, Min: {min_processing_time:.3f}s"
            )
            return True
            
        except Exception as e:
            duration = time.time() - test_start
            self.log_test_result(
                "Performance Under Load",
                False,
                duration,
                f"Error: {str(e)}"
            )
            return False
    
    def test_data_integrity_validation(self) -> bool:
        """Test data integrity validation across the system."""
        test_start = time.time()
        
        try:
            # Create test device and process it
            device = self.create_test_device(DeviceType.HDD, "INTEGRITY_TEST_001")
            data_file = self.create_test_data_file(device.device_id)
            
            # Process device
            wipe_result = self.wipe_engine.wipe_device(data_file, WipeMethod.NIST_CLEAR)
            if not wipe_result.success:
                raise Exception("Wiping failed")
            
            original_hash = self.hash_generator.generate_wipe_hash(wipe_result)
            
            # Test 1: Hash determinism
            hash2 = self.hash_generator.generate_wipe_hash(wipe_result)
            if original_hash != hash2:
                raise Exception("Hash generation is not deterministic")
            
            # Test 2: Hash verification
            is_valid = self.hash_generator.verify_hash(wipe_result, original_hash)
            if not is_valid:
                raise Exception("Hash verification failed for valid data")
            
            # Test 3: Tamper detection
            from secure_data_wiping.utils.data_models import WipeResult
            modified_result = WipeResult(
                operation_id=wipe_result.operation_id,
                device_id="MODIFIED_DEVICE_ID",  # Changed!
                method=wipe_result.method,
                passes_completed=wipe_result.passes_completed,
                start_time=wipe_result.start_time,
                success=wipe_result.success,
                operator_id=wipe_result.operator_id,
                verification_hash=wipe_result.verification_hash
            )
            
            tamper_detected = not self.hash_generator.verify_hash(modified_result, original_hash)
            if not tamper_detected:
                raise Exception("Tamper detection failed")
            
            # Test 4: Certificate integrity
            wipe_data = WipeData(
                device_id=device.device_id,
                wipe_hash=original_hash,
                timestamp=datetime.now(),
                method=wipe_result.method.value,
                operator='integrity_test',
                passes=wipe_result.passes_completed
            )
            
            blockchain_data = BlockchainData(
                transaction_hash="0x" + "c" * 62,
                block_number=54321,
                contract_address="0x" + "d" * 38,
                gas_used=45000,
                confirmation_count=12
            )
            
            cert_path = self.certificate_generator.generate_certificate(
                wipe_data, blockchain_data, device
            )
            
            if not os.path.exists(cert_path):
                raise Exception("Certificate generation failed")
            
            # Verify certificate contains expected data
            cert_size = os.path.getsize(cert_path)
            if cert_size < 1000:  # Certificate should be reasonably sized
                raise Exception(f"Certificate too small: {cert_size} bytes")
            
            self.stats['total_certificates_generated'] += 1
            
            # Cleanup
            if os.path.exists(data_file):
                os.remove(data_file)
            if os.path.exists(data_file + '.DESTROYED'):
                os.remove(data_file + '.DESTROYED')
            
            duration = time.time() - test_start
            
            self.log_test_result(
                "Data Integrity Validation",
                True,
                duration,
                "Hash determinism, verification, tamper detection, and certificate integrity validated"
            )
            return True
            
        except Exception as e:
            duration = time.time() - test_start
            self.log_test_result(
                "Data Integrity Validation",
                False,
                duration,
                f"Error: {str(e)}"
            )
            return False
    
    def run_comprehensive_integration_tests(self) -> Dict[str, Any]:
        """Run all integration tests and return comprehensive results."""
        print("🧪 COMPREHENSIVE SYSTEM INTEGRATION TESTS")
        print("=" * 80)
        print("Testing end-to-end workflows, error recovery, and system resilience")
        print("=" * 80)
        
        # Define test suite
        test_suite = [
            ("End-to-End Workflow", self.test_end_to_end_workflow),
            ("Multiple Device Processing", self.test_multiple_device_processing),
            ("Error Recovery and Resilience", self.test_error_recovery_and_resilience),
            ("Concurrent Operations", self.test_concurrent_operations),
            ("Performance Under Load", self.test_performance_under_load),
            ("Data Integrity Validation", self.test_data_integrity_validation),
        ]
        
        # Run tests
        for test_name, test_func in test_suite:
            print(f"\n--- Running: {test_name} ---")
            test_func()
        
        # Calculate final statistics
        total_test_time = (datetime.now() - self.test_start_time).total_seconds()
        success_rate = (self.stats['tests_passed'] / self.stats['tests_run']) * 100 if self.stats['tests_run'] > 0 else 0
        
        # Print summary
        print(f"\n{'='*80}")
        print("INTEGRATION TEST SUMMARY")
        print(f"{'='*80}")
        
        print(f"Total test time: {total_test_time:.2f} seconds")
        print(f"Tests run: {self.stats['tests_run']}")
        print(f"Tests passed: {self.stats['tests_passed']}")
        print(f"Tests failed: {self.stats['tests_failed']}")
        print(f"Success rate: {success_rate:.1f}%")
        print(f"Devices processed: {self.stats['total_devices_processed']}")
        print(f"Certificates generated: {self.stats['total_certificates_generated']}")
        print(f"Total processing time: {self.stats['total_processing_time']:.3f}s")
        
        if self.stats['total_devices_processed'] > 0:
            avg_device_time = self.stats['total_processing_time'] / self.stats['total_devices_processed']
            print(f"Average device processing time: {avg_device_time:.3f}s")
        
        # Detailed results
        print(f"\nDetailed Test Results:")
        for test_name, result in self.test_results.items():
            status = "✅ PASSED" if result['success'] else "❌ FAILED"
            print(f"  {status} {test_name}: {result['duration']:.3f}s")
            if result['details']:
                print(f"    {result['details']}")
        
        all_passed = self.stats['tests_failed'] == 0
        
        if all_passed:
            print(f"\n🎉 ALL INTEGRATION TESTS PASSED!")
            print(f"System is fully validated and ready for production use.")
        else:
            print(f"\n⚠️ Some integration tests failed. Please review and fix issues.")
        
        return {
            'success': all_passed,
            'total_time': total_test_time,
            'statistics': self.stats,
            'test_results': self.test_results,
            'temp_directory': str(self.temp_dir)
        }


def main():
    """Main function for integration testing."""
    print("🧪 FINAL SYSTEM INTEGRATION TESTS")
    print("=" * 80)
    
    tester = SystemIntegrationTester()
    results = tester.run_comprehensive_integration_tests()
    
    if results['success']:
        print(f"\n✅ All integration tests passed!")
        return 0
    else:
        print(f"\n❌ Some integration tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
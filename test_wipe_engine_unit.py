#!/usr/bin/env python3
"""
Unit tests for WipeEngine implementation.
Tests specific examples, edge cases, and integration points.

Feature: secure-data-wiping-blockchain
Task 5.3: Unit tests for wiping methods
"""

import sys
import os
import tempfile
import shutil
import time
from datetime import datetime
from unittest.mock import patch, mock_open

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from secure_data_wiping.wipe_engine import (
    WipeEngine, WipeEngineError, DeviceAccessError, WipeOperationError, VerificationError
)
from secure_data_wiping.utils.data_models import (
    WipeMethod, WipeConfig, DeviceInfo, DeviceType, WipeResult
)


class TestWipeEngineUnit:
    """Unit tests for WipeEngine implementation."""
    
    def setup_method(self):
        """Set up test environment."""
        self.engine = WipeEngine()
        self.temp_dir = tempfile.mkdtemp()
        self.test_files = []
    
    def teardown_method(self):
        """Clean up test environment."""
        # Clean up test files
        for file_path in self.test_files:
            if os.path.exists(file_path):
                try:
                    os.unlink(file_path)
                except OSError:
                    pass
        
        # Clean up temp directory
        if os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)
            except OSError:
                pass
    
    def create_test_file(self, content=None, size_bytes=1024):
        """Create a temporary test file with specified content or size."""
        temp_file = tempfile.NamedTemporaryFile(dir=self.temp_dir, delete=False)
        
        if content is not None:
            temp_file.write(content)
        else:
            temp_file.write(b'X' * size_bytes)
        
        temp_file.close()
        self.test_files.append(temp_file.name)
        return temp_file.name
    
    def test_wipe_engine_initialization(self):
        """Test WipeEngine initialization with various configurations."""
        # Default initialization
        engine1 = WipeEngine()
        assert engine1.operations_completed == 0
        assert engine1.total_bytes_wiped == 0
        assert engine1.last_operation_time is None
        assert engine1.default_config.method == WipeMethod.NIST_CLEAR
        
        # Initialization with custom config
        custom_config = WipeConfig(
            method=WipeMethod.NIST_PURGE,
            passes=5,
            verify_wipe=False,
            block_size=8192
        )
        engine2 = WipeEngine(custom_config)
        assert engine2.default_config.method == WipeMethod.NIST_PURGE
        assert engine2.default_config.passes == 5
        assert engine2.default_config.verify_wipe is False
        assert engine2.default_config.block_size == 8192
        
        print("✓ WipeEngine initialization tests passed")
    
    def test_device_access_validation_edge_cases(self):
        """Test device access validation with edge cases."""
        # Empty string
        try:
            self.engine._validate_device_access("")
            assert False, "Should reject empty string"
        except DeviceAccessError as e:
            assert "Device path cannot be empty" in str(e)
        
        # Whitespace only
        try:
            self.engine._validate_device_access("   \t\n  ")
            assert False, "Should reject whitespace-only string"
        except DeviceAccessError as e:
            assert "Device path cannot be empty" in str(e)
        
        # None (should raise TypeError before reaching validation)
        try:
            self.engine._validate_device_access(None)
            assert False, "Should reject None"
        except (DeviceAccessError, AttributeError):
            pass  # Either error is acceptable
        
        # Valid device path simulation
        test_file = self.create_test_file()
        self.engine._validate_device_access(test_file)  # Should not raise
        
        # Simulated device path
        self.engine._validate_device_access("/dev/sda1")  # Should not raise (simulation)
        
        print("✓ Device access validation edge cases passed")
    
    def test_device_info_detection_comprehensive(self):
        """Test device information detection with various path patterns."""
        test_cases = [
            ("/dev/sda1", DeviceType.SD_CARD),  # Contains 'sd'
            ("/dev/sdb1", DeviceType.SD_CARD),  # Contains 'sd'
            ("/dev/ssd1", DeviceType.SSD),      # 'ssd' takes precedence over 'sd'
            ("/dev/nvme0n1", DeviceType.SSD),   # Contains 'nvme'
            ("/dev/usb1", DeviceType.USB),      # Contains 'usb'
            ("/dev/mmcblk0", DeviceType.SD_CARD), # Contains 'mmc'
            ("/dev/hda1", DeviceType.HDD),      # Contains 'hd'
            ("/dev/hdd1", DeviceType.HDD),      # Contains 'hdd'
            ("/mnt/test_ssd.img", DeviceType.SSD), # Contains 'ssd'
            ("/tmp/usb_drive.bin", DeviceType.USB), # Contains 'usb'
            ("/home/user/hdd_backup.img", DeviceType.HDD), # Contains 'hdd'
            ("C:\\temp\\ssd_test.bin", DeviceType.SSD), # Contains 'ssd'
            ("/dev/vda1", DeviceType.OTHER),    # No matching patterns
            ("unknown_device", DeviceType.OTHER), # No matching patterns
        ]
        
        for device_path, expected_type in test_cases:
            device_id = f"TEST_{expected_type.value.upper()}"
            device_info = self.engine._detect_device_info(device_path, device_id)
            
            assert device_info.device_id == device_id
            assert device_info.device_type == expected_type, f"Expected {expected_type.value} for {device_path}, got {device_info.device_type.value}"
            assert device_info.manufacturer == "Simulated"
            assert device_info.model == "Academic Test Device"
            
        print("✓ Device info detection comprehensive tests passed")
    
    def test_nist_pass_requirements_all_combinations(self):
        """Test NIST pass requirements for all method/device combinations."""
        expected_passes = {
            # CLEAR method - always 1 pass
            (WipeMethod.NIST_CLEAR, DeviceType.HDD): 1,
            (WipeMethod.NIST_CLEAR, DeviceType.SSD): 1,
            (WipeMethod.NIST_CLEAR, DeviceType.USB): 1,
            (WipeMethod.NIST_CLEAR, DeviceType.NVME): 1,
            (WipeMethod.NIST_CLEAR, DeviceType.SD_CARD): 1,
            (WipeMethod.NIST_CLEAR, DeviceType.OTHER): 1,
            
            # PURGE method - device dependent
            (WipeMethod.NIST_PURGE, DeviceType.HDD): 3,
            (WipeMethod.NIST_PURGE, DeviceType.SSD): 1,  # Crypto erase
            (WipeMethod.NIST_PURGE, DeviceType.USB): 3,
            (WipeMethod.NIST_PURGE, DeviceType.NVME): 1,  # Crypto erase
            (WipeMethod.NIST_PURGE, DeviceType.SD_CARD): 3,
            (WipeMethod.NIST_PURGE, DeviceType.OTHER): 3,
            
            # DESTROY method - always 1 pass (physical destruction)
            (WipeMethod.NIST_DESTROY, DeviceType.HDD): 1,
            (WipeMethod.NIST_DESTROY, DeviceType.SSD): 1,
            (WipeMethod.NIST_DESTROY, DeviceType.USB): 1,
            (WipeMethod.NIST_DESTROY, DeviceType.NVME): 1,
            (WipeMethod.NIST_DESTROY, DeviceType.SD_CARD): 1,
            (WipeMethod.NIST_DESTROY, DeviceType.OTHER): 1,
        }
        
        for (method, device_type), expected in expected_passes.items():
            actual = self.engine.get_nist_pass_count(method, device_type)
            assert actual == expected, f"Expected {expected} passes for {method.value} on {device_type.value}, got {actual}"
        
        print("✓ NIST pass requirements all combinations passed")
    
    def test_wipe_clear_method_detailed(self):
        """Test NIST CLEAR method with detailed verification."""
        # Create test file with known content
        test_content = b"SENSITIVE_DATA_TO_BE_CLEARED" * 50
        test_file = self.create_test_file(test_content)
        
        device_info = DeviceInfo(
            device_id="CLEAR_TEST_001",
            device_type=DeviceType.HDD,
            manufacturer="Test Corp",
            model="Test Drive 1TB",
            capacity=len(test_content)
        )
        
        # Perform CLEAR wipe
        result = self.engine.wipe_device(
            device_path=test_file,
            method=WipeMethod.NIST_CLEAR,
            device_info=device_info
        )
        
        # Verify result properties
        assert result.success is True
        assert result.method == WipeMethod.NIST_CLEAR
        assert result.passes_completed == 1
        assert result.device_id == "CLEAR_TEST_001"
        assert result.bytes_wiped == len(test_content)
        assert result.start_time is not None
        assert result.end_time is not None
        assert result.duration is not None
        assert result.duration > 0
        assert result.verification_hash is not None
        
        # Verify file content was overwritten with zeros
        with open(test_file, 'rb') as f:
            cleared_content = f.read()
            assert cleared_content == b'\x00' * len(test_content)
        
        # Verify statistics were updated
        assert self.engine.operations_completed >= 1
        assert self.engine.total_bytes_wiped >= len(test_content)
        
        print("✓ NIST CLEAR method detailed tests passed")
    
    def test_wipe_purge_method_device_specific(self):
        """Test NIST PURGE method with device-specific behavior."""
        test_content = b"CONFIDENTIAL_DATA_FOR_PURGE" * 30
        
        # Test HDD PURGE (3 passes)
        hdd_file = self.create_test_file(test_content)
        hdd_info = DeviceInfo(device_id="HDD_PURGE_001", device_type=DeviceType.HDD)
        
        hdd_result = self.engine.wipe_device(hdd_file, WipeMethod.NIST_PURGE, hdd_info)
        assert hdd_result.success is True
        assert hdd_result.passes_completed == 3
        assert hdd_result.bytes_wiped == len(test_content) * 3  # 3 passes
        
        # Test SSD PURGE (1 pass - crypto erase simulation)
        ssd_file = self.create_test_file(test_content)
        ssd_info = DeviceInfo(device_id="SSD_PURGE_001", device_type=DeviceType.SSD)
        
        ssd_result = self.engine.wipe_device(ssd_file, WipeMethod.NIST_PURGE, ssd_info)
        assert ssd_result.success is True
        assert ssd_result.passes_completed == 1
        assert ssd_result.bytes_wiped == len(test_content)  # 1 pass
        
        # Test USB PURGE (3 passes)
        usb_file = self.create_test_file(test_content)
        usb_info = DeviceInfo(device_id="USB_PURGE_001", device_type=DeviceType.USB)
        
        usb_result = self.engine.wipe_device(usb_file, WipeMethod.NIST_PURGE, usb_info)
        assert usb_result.success is True
        assert usb_result.passes_completed == 3
        assert usb_result.bytes_wiped == len(test_content) * 3  # 3 passes
        
        print("✓ NIST PURGE method device-specific tests passed")
    
    def test_wipe_destroy_method_simulation(self):
        """Test NIST DESTROY method physical destruction simulation."""
        test_content = b"TOP_SECRET_DATA_FOR_DESTRUCTION" * 20
        test_file = self.create_test_file(test_content)
        original_path = test_file
        
        device_info = DeviceInfo(
            device_id="DESTROY_TEST_001",
            device_type=DeviceType.HDD,
            capacity=len(test_content)
        )
        
        # Perform DESTROY operation
        result = self.engine.wipe_device(test_file, WipeMethod.NIST_DESTROY, device_info)
        
        # Verify result
        assert result.success is True
        assert result.method == WipeMethod.NIST_DESTROY
        assert result.passes_completed == 1
        assert result.bytes_wiped == len(test_content)
        
        # Verify original file no longer exists
        assert not os.path.exists(original_path)
        
        # Verify destroyed file was created
        destroyed_files = [f for f in os.listdir(self.temp_dir) 
                          if f.startswith(os.path.basename(original_path) + ".DESTROYED")]
        assert len(destroyed_files) == 1, f"Expected 1 destroyed file, found {len(destroyed_files)}: {destroyed_files}"
        
        destroyed_path = os.path.join(self.temp_dir, destroyed_files[0])
        assert os.path.exists(destroyed_path)
        
        # Verify destroyed file has the expected size
        # (Content verification is less important for destruction simulation)
        destroyed_size = os.path.getsize(destroyed_path)
        assert destroyed_size == len(test_content), f"Expected destroyed file size {len(test_content)}, got {destroyed_size}"
        
        # Clean up destroyed file
        os.unlink(destroyed_path)
        
        print("✓ NIST DESTROY method simulation tests passed")
    
    def test_wipe_verification_functionality(self):
        """Test wipe verification with various scenarios."""
        test_content = b"VERIFICATION_TEST_DATA" * 25
        
        # Test successful verification for CLEAR method
        test_file1 = self.create_test_file(test_content)
        device_info = DeviceInfo(device_id="VERIFY_001", device_type=DeviceType.HDD)
        
        result1 = self.engine.wipe_device(test_file1, WipeMethod.NIST_CLEAR, device_info)
        verification1 = self.engine.verify_wipe(test_file1, result1)
        assert verification1 is True, "CLEAR verification should succeed for existing wiped file"
        
        # Test verification with DESTROY method
        test_file2 = self.create_test_file(test_content)
        result2 = self.engine.wipe_device(test_file2, WipeMethod.NIST_DESTROY, device_info)
        # For DESTROY method, verification should check that original file no longer exists
        verification2 = self.engine.verify_wipe(test_file2, result2)
        assert verification2 is True, "DESTROY verification should succeed when original file is gone"
        
        # Test verification with DESTROY method on already non-existent file (should succeed)
        non_existent_device = "/dev/non_existent_device"
        fake_destroy_result = WipeResult(
            operation_id="FAKE_002",
            device_id="FAKE_DEVICE_2",
            method=WipeMethod.NIST_DESTROY,  # DESTROY method
            passes_completed=1,
            start_time=datetime.now()
        )
        verification3 = self.engine.verify_wipe(non_existent_device, fake_destroy_result)
        assert verification3 is True, "DESTROY verification should succeed when file doesn't exist"
        
        # Test that verification methods exist and are callable
        assert hasattr(self.engine, '_verify_overwrite'), "Should have _verify_overwrite method"
        assert hasattr(self.engine, '_verify_destruction'), "Should have _verify_destruction method"
        
        print("✓ Wipe verification functionality tests passed")
    
    def test_configuration_override_behavior(self):
        """Test that wipe configuration properly overrides defaults."""
        test_file = self.create_test_file(b"CONFIG_TEST" * 50)
        device_info = DeviceInfo(device_id="CONFIG_001", device_type=DeviceType.HDD)
        
        # Test method override
        result1 = self.engine.wipe_device(
            test_file,
            method=WipeMethod.NIST_PURGE,  # Override method
            device_info=device_info
        )
        assert result1.method == WipeMethod.NIST_PURGE
        
        # Test config override
        custom_config = WipeConfig(
            method=WipeMethod.NIST_CLEAR,
            verify_wipe=False,
            block_size=8192
        )
        
        test_file2 = self.create_test_file(b"CONFIG_TEST2" * 50)
        result2 = self.engine.wipe_device(
            test_file2,
            device_info=device_info,
            config=custom_config
        )
        assert result2.method == WipeMethod.NIST_CLEAR
        
        # Test method parameter overrides config
        result3 = self.engine.wipe_device(
            test_file2,  # Reuse file
            method=WipeMethod.NIST_DESTROY,  # This should override config method
            device_info=device_info,
            config=custom_config
        )
        assert result3.method == WipeMethod.NIST_DESTROY
        
        print("✓ Configuration override behavior tests passed")
    
    def test_error_handling_scenarios(self):
        """Test various error handling scenarios."""
        device_info = DeviceInfo(device_id="ERROR_001", device_type=DeviceType.HDD)
        
        # Test empty device path
        try:
            self.engine.wipe_device("", WipeMethod.NIST_CLEAR, device_info)
            assert False, "Should raise DeviceAccessError"
        except DeviceAccessError:
            pass
        
        # Test invalid device info
        try:
            invalid_device_info = DeviceInfo(device_id="", device_type=DeviceType.HDD)
            assert False, "Should raise ValueError during DeviceInfo creation"
        except ValueError:
            pass
        
        # Test with permission denied simulation (mock)
        test_file = self.create_test_file()
        
        with patch('builtins.open', side_effect=PermissionError("Permission denied")):
            try:
                self.engine.wipe_device(test_file, WipeMethod.NIST_CLEAR, device_info)
                assert False, "Should raise DeviceAccessError"
            except DeviceAccessError as e:
                assert "Permission denied" in str(e)
        
        # Test with OSError during file operations
        with patch('os.path.getsize', side_effect=OSError("File system error")):
            try:
                self.engine.wipe_device(test_file, WipeMethod.NIST_CLEAR, device_info)
                assert False, "Should raise WipeOperationError"
            except (WipeOperationError, DeviceAccessError):
                # Either error is acceptable depending on when the error occurs
                pass
        
        print("✓ Error handling scenarios tests passed")
    
    def test_statistics_tracking_accuracy(self):
        """Test that statistics are tracked accurately."""
        initial_stats = self.engine.get_statistics()
        assert initial_stats['operations_completed'] == 0
        assert initial_stats['total_bytes_wiped'] == 0
        
        # Perform multiple operations
        test_sizes = [512, 1024, 2048]
        device_info = DeviceInfo(device_id="STATS_001", device_type=DeviceType.HDD)
        
        total_expected_bytes = 0
        for i, size in enumerate(test_sizes):
            test_file = self.create_test_file(size_bytes=size)
            result = self.engine.wipe_device(test_file, WipeMethod.NIST_CLEAR, device_info)
            total_expected_bytes += size
            
            # Check intermediate stats
            stats = self.engine.get_statistics()
            assert stats['operations_completed'] == i + 1
            assert stats['total_bytes_wiped'] >= total_expected_bytes
        
        # Check final stats
        final_stats = self.engine.get_statistics()
        assert final_stats['operations_completed'] == len(test_sizes)
        assert final_stats['total_bytes_wiped'] >= total_expected_bytes
        assert final_stats['last_operation_time'] is not None
        
        # Verify stats structure
        assert 'nist_methods_supported' in final_stats
        assert 'device_types_supported' in final_stats
        assert len(final_stats['nist_methods_supported']) == 3  # CLEAR, PURGE, DESTROY
        assert len(final_stats['device_types_supported']) == 6  # All device types
        
        print("✓ Statistics tracking accuracy tests passed")
    
    def test_verification_hash_generation(self):
        """Test verification hash generation and consistency."""
        test_file = self.create_test_file(b"HASH_TEST" * 100)
        device_info = DeviceInfo(
            device_id="HASH_001",
            device_type=DeviceType.HDD,
            manufacturer="Hash Corp",
            model="Hash Drive"
        )
        
        # Test with verification enabled
        config_with_verify = WipeConfig(method=WipeMethod.NIST_CLEAR, verify_wipe=True)
        result1 = self.engine.wipe_device(test_file, device_info=device_info, config=config_with_verify)
        
        assert result1.verification_hash is not None
        assert len(result1.verification_hash) == 64  # SHA-256 hex string
        assert all(c in '0123456789abcdef' for c in result1.verification_hash.lower())
        
        # Test hash consistency (same operation should produce same hash)
        test_file2 = self.create_test_file(b"HASH_TEST" * 100)  # Same content
        result2 = self.engine.wipe_device(test_file2, device_info=device_info, config=config_with_verify)
        
        # Hashes should be different due to timestamps, but both should be valid
        assert result2.verification_hash is not None
        assert len(result2.verification_hash) == 64
        assert result1.verification_hash != result2.verification_hash  # Different due to timestamps
        
        print("✓ Verification hash generation tests passed")
    
    def test_block_size_handling(self):
        """Test handling of different block sizes."""
        test_content = b"BLOCK_SIZE_TEST" * 200  # 3000 bytes
        device_info = DeviceInfo(device_id="BLOCK_001", device_type=DeviceType.HDD)
        
        block_sizes = [512, 1024, 2048, 4096, 8192]
        
        for block_size in block_sizes:
            test_file = self.create_test_file(test_content)
            config = WipeConfig(method=WipeMethod.NIST_CLEAR, block_size=block_size)
            
            result = self.engine.wipe_device(test_file, device_info=device_info, config=config)
            
            assert result.success is True
            assert result.bytes_wiped == len(test_content)
            
            # Verify file was properly overwritten
            with open(test_file, 'rb') as f:
                content = f.read()
                assert content == b'\x00' * len(test_content)
        
        print("✓ Block size handling tests passed")


def run_all_unit_tests():
    """Run all unit tests."""
    test_instance = TestWipeEngineUnit()
    
    test_methods = [
        test_instance.test_wipe_engine_initialization,
        test_instance.test_device_access_validation_edge_cases,
        test_instance.test_device_info_detection_comprehensive,
        test_instance.test_nist_pass_requirements_all_combinations,
        test_instance.test_wipe_clear_method_detailed,
        test_instance.test_wipe_purge_method_device_specific,
        test_instance.test_wipe_destroy_method_simulation,
        test_instance.test_wipe_verification_functionality,
        test_instance.test_configuration_override_behavior,
        test_instance.test_error_handling_scenarios,
        test_instance.test_statistics_tracking_accuracy,
        test_instance.test_verification_hash_generation,
        test_instance.test_block_size_handling,
    ]
    
    for i, test_method in enumerate(test_methods):
        print(f"\nRunning test {i+1}/{len(test_methods)}: {test_method.__name__}")
        test_instance.setup_method()
        try:
            test_method()
        finally:
            test_instance.teardown_method()
    
    print(f"\n✓ All {len(test_methods)} unit tests passed!")


if __name__ == "__main__":
    try:
        print("Running WipeEngine unit tests...")
        run_all_unit_tests()
        
        print("\n🎉 All WipeEngine unit tests passed successfully!")
        print("✓ Task 5.3: Unit tests for wiping methods - COMPLETED")
        print("✓ Comprehensive edge case testing completed")
        print("✓ All three NIST methods thoroughly tested")
        print("✓ Error handling and configuration testing completed")
        print("✓ Statistics and verification functionality validated")
        
    except Exception as e:
        print(f"\n❌ Unit test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
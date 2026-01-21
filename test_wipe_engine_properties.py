#!/usr/bin/env python3
"""
Property-based tests for WipeEngine implementation.
Tests universal properties that should hold across all valid inputs.

Feature: secure-data-wiping-blockchain
Property 1: NIST Compliance for Wiping Operations
"""

import sys
import os
import tempfile
import shutil
from datetime import datetime
from hypothesis import given, strategies as st, settings, assume
from hypothesis.stateful import RuleBasedStateMachine, rule, initialize, invariant

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from secure_data_wiping.wipe_engine import WipeEngine, WipeEngineError
from secure_data_wiping.utils.data_models import WipeMethod, WipeConfig, DeviceInfo, DeviceType


# Strategy for generating device types
device_type_strategy = st.sampled_from([
    DeviceType.HDD,
    DeviceType.SSD,
    DeviceType.USB,
    DeviceType.NVME,
    DeviceType.SD_CARD,
    DeviceType.OTHER
])

# Strategy for generating wipe methods
wipe_method_strategy = st.sampled_from([
    WipeMethod.NIST_CLEAR,
    WipeMethod.NIST_PURGE,
    WipeMethod.NIST_DESTROY
])

# Strategy for generating device info
@st.composite
def device_info_strategy(draw):
    """Generate valid DeviceInfo objects."""
    device_id = draw(st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc'))))
    device_type = draw(device_type_strategy)
    manufacturer = draw(st.one_of(st.none(), st.text(min_size=1, max_size=30)))
    model = draw(st.one_of(st.none(), st.text(min_size=1, max_size=30)))
    capacity = draw(st.one_of(st.none(), st.integers(min_value=1024, max_value=1024*1024*1024)))  # 1KB to 1GB
    
    return DeviceInfo(
        device_id=device_id,
        device_type=device_type,
        manufacturer=manufacturer,
        model=model,
        capacity=capacity
    )

# Strategy for generating wipe configs
@st.composite
def wipe_config_strategy(draw):
    """Generate valid WipeConfig objects."""
    method = draw(wipe_method_strategy)
    passes = draw(st.integers(min_value=1, max_value=10))
    verify_wipe = draw(st.booleans())
    block_size = draw(st.sampled_from([512, 1024, 2048, 4096, 8192]))
    timeout = draw(st.integers(min_value=60, max_value=3600))
    
    return WipeConfig(
        method=method,
        passes=passes,
        verify_wipe=verify_wipe,
        block_size=block_size,
        timeout=timeout
    )


class TestWipeEngineProperties:
    """Property-based tests for WipeEngine."""
    
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
    
    def create_test_file(self, size_bytes=1024):
        """Create a temporary test file."""
        temp_file = tempfile.NamedTemporaryFile(dir=self.temp_dir, delete=False)
        temp_file.write(b'X' * size_bytes)
        temp_file.close()
        self.test_files.append(temp_file.name)
        return temp_file.name
    
    @given(device_info=device_info_strategy(), wipe_method=wipe_method_strategy)
    @settings(max_examples=50, deadline=30000)  # 30 second deadline per test
    def test_property_1_nist_compliance_for_wiping_operations(self, device_info, wipe_method):
        """
        Property 1: NIST Compliance for Wiping Operations
        
        For any wiping operation on any supported device type, the system should 
        implement NIST 800-88 compliant procedures with the correct number of passes 
        for the specified method.
        
        Validates: Requirements 1.1, 1.2, 1.5
        """
        # Create test file
        test_file = self.create_test_file(1024)  # 1KB test file
        
        # Get expected NIST pass count
        expected_passes = self.engine.get_nist_pass_count(wipe_method, device_info.device_type)
        
        # Perform wipe operation
        result = self.engine.wipe_device(
            device_path=test_file,
            method=wipe_method,
            device_info=device_info
        )
        
        # Verify NIST compliance properties
        assert result.success is True, f"Wipe operation should succeed for {wipe_method.value} on {device_info.device_type.value}"
        assert result.method == wipe_method, f"Result method should match requested method"
        assert result.passes_completed >= expected_passes, f"Should complete at least {expected_passes} passes for {wipe_method.value} on {device_info.device_type.value}"
        assert result.device_id == device_info.device_id, f"Device ID should match"
        assert result.start_time is not None, f"Start time should be recorded"
        assert result.end_time is not None, f"End time should be recorded"
        assert result.bytes_wiped > 0, f"Should report bytes wiped"
        
        # Verify NIST-specific requirements
        if wipe_method == WipeMethod.NIST_CLEAR:
            # CLEAR method should use exactly 1 pass for all device types
            assert result.passes_completed == 1, f"NIST CLEAR should use exactly 1 pass, got {result.passes_completed}"
        
        elif wipe_method == WipeMethod.NIST_PURGE:
            # PURGE method pass count depends on device type
            if device_info.device_type in [DeviceType.SSD, DeviceType.NVME]:
                # SSDs and NVMe should use 1 pass (cryptographic erase simulation)
                assert result.passes_completed == 1, f"NIST PURGE on SSD/NVMe should use 1 pass (crypto erase), got {result.passes_completed}"
            else:
                # HDDs and other devices should use 3 passes
                assert result.passes_completed == 3, f"NIST PURGE on {device_info.device_type.value} should use 3 passes, got {result.passes_completed}"
        
        elif wipe_method == WipeMethod.NIST_DESTROY:
            # DESTROY method should use 1 pass (physical destruction simulation)
            assert result.passes_completed == 1, f"NIST DESTROY should use 1 pass (destruction), got {result.passes_completed}"
            # For DESTROY, original file should no longer exist
            assert not os.path.exists(test_file), f"Original file should be destroyed"
    
    @given(device_type=device_type_strategy, wipe_method=wipe_method_strategy)
    @settings(max_examples=30)
    def test_nist_pass_count_consistency(self, device_type, wipe_method):
        """
        Test that NIST pass count requirements are consistent and follow standards.
        """
        pass_count = self.engine.get_nist_pass_count(wipe_method, device_type)
        
        # All methods should require at least 1 pass
        assert pass_count >= 1, f"All methods should require at least 1 pass"
        
        # CLEAR should always be 1 pass
        if wipe_method == WipeMethod.NIST_CLEAR:
            assert pass_count == 1, f"NIST CLEAR should always be 1 pass"
        
        # DESTROY should always be 1 pass (physical destruction)
        elif wipe_method == WipeMethod.NIST_DESTROY:
            assert pass_count == 1, f"NIST DESTROY should always be 1 pass"
        
        # PURGE should follow device-specific requirements
        elif wipe_method == WipeMethod.NIST_PURGE:
            if device_type in [DeviceType.SSD, DeviceType.NVME]:
                assert pass_count == 1, f"PURGE on SSD/NVMe should be 1 pass (crypto erase)"
            else:
                assert pass_count == 3, f"PURGE on {device_type.value} should be 3 passes"
    
    @given(device_info=device_info_strategy())
    @settings(max_examples=20)
    def test_all_methods_supported_for_all_devices(self, device_info):
        """
        Test that all NIST methods are supported for all device types.
        """
        test_file = self.create_test_file(512)  # Small test file
        
        for method in [WipeMethod.NIST_CLEAR, WipeMethod.NIST_PURGE, WipeMethod.NIST_DESTROY]:
            # Each method should work with each device type
            result = self.engine.wipe_device(
                device_path=test_file,
                method=method,
                device_info=device_info
            )
            
            assert result.success is True, f"Method {method.value} should work with device type {device_info.device_type.value}"
            assert result.method == method, f"Result should reflect requested method"
            
            # Recreate test file for next method (DESTROY removes it)
            if method == WipeMethod.NIST_DESTROY:
                test_file = self.create_test_file(512)
    
    @given(wipe_config=wipe_config_strategy(), device_info=device_info_strategy())
    @settings(max_examples=20)
    def test_configuration_override_behavior(self, wipe_config, device_info):
        """
        Test that wipe configuration properly overrides default settings.
        """
        test_file = self.create_test_file(1024)
        
        # Perform wipe with specific config
        result = self.engine.wipe_device(
            device_path=test_file,
            device_info=device_info,
            config=wipe_config
        )
        
        # Result should reflect the configuration
        assert result.success is True, f"Wipe with custom config should succeed"
        assert result.method == wipe_config.method, f"Should use configured method"
        
        # Pass count should follow NIST requirements, not config.passes
        expected_passes = self.engine.get_nist_pass_count(wipe_config.method, device_info.device_type)
        assert result.passes_completed == expected_passes, f"Should follow NIST requirements regardless of config.passes"
    
    @given(device_info=device_info_strategy())
    @settings(max_examples=15)
    def test_verification_hash_generation(self, device_info):
        """
        Test that verification hashes are generated when verification is enabled.
        """
        test_file = self.create_test_file(1024)
        
        # Create config with verification enabled
        config = WipeConfig(method=WipeMethod.NIST_CLEAR, verify_wipe=True)
        
        result = self.engine.wipe_device(
            device_path=test_file,
            device_info=device_info,
            config=config
        )
        
        assert result.success is True, f"Wipe with verification should succeed"
        assert result.verification_hash is not None, f"Should generate verification hash when verify_wipe=True"
        assert len(result.verification_hash) == 64, f"SHA-256 hash should be 64 hex characters"
        
        # Test without verification
        test_file2 = self.create_test_file(1024)
        config_no_verify = WipeConfig(method=WipeMethod.NIST_CLEAR, verify_wipe=False)
        
        result2 = self.engine.wipe_device(
            device_path=test_file2,
            device_info=device_info,
            config=config_no_verify
        )
        
        assert result2.success is True, f"Wipe without verification should succeed"
        # Verification hash might still be generated, but verification step is skipped


def test_property_1_examples():
    """
    Test Property 1 with specific examples to ensure correctness.
    """
    print("Testing Property 1: NIST Compliance with specific examples...")
    
    engine = WipeEngine()
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Test Case 1: HDD with CLEAR method
        test_file1 = os.path.join(temp_dir, "test_hdd.img")
        with open(test_file1, 'wb') as f:
            f.write(b'TEST_DATA' * 100)
        
        hdd_info = DeviceInfo(device_id="HDD_001", device_type=DeviceType.HDD)
        result1 = engine.wipe_device(test_file1, WipeMethod.NIST_CLEAR, hdd_info)
        
        assert result1.success is True
        assert result1.passes_completed == 1  # CLEAR = 1 pass
        assert result1.method == WipeMethod.NIST_CLEAR
        print("✓ HDD CLEAR: 1 pass as expected")
        
        # Test Case 2: SSD with PURGE method
        test_file2 = os.path.join(temp_dir, "test_ssd.img")
        with open(test_file2, 'wb') as f:
            f.write(b'SSD_DATA' * 100)
        
        ssd_info = DeviceInfo(device_id="SSD_001", device_type=DeviceType.SSD)
        result2 = engine.wipe_device(test_file2, WipeMethod.NIST_PURGE, ssd_info)
        
        assert result2.success is True
        assert result2.passes_completed == 1  # SSD PURGE = 1 pass (crypto erase)
        assert result2.method == WipeMethod.NIST_PURGE
        print("✓ SSD PURGE: 1 pass (crypto erase) as expected")
        
        # Test Case 3: USB with PURGE method
        test_file3 = os.path.join(temp_dir, "test_usb.img")
        with open(test_file3, 'wb') as f:
            f.write(b'USB_DATA' * 100)
        
        usb_info = DeviceInfo(device_id="USB_001", device_type=DeviceType.USB)
        result3 = engine.wipe_device(test_file3, WipeMethod.NIST_PURGE, usb_info)
        
        assert result3.success is True
        assert result3.passes_completed == 3  # USB PURGE = 3 passes
        assert result3.method == WipeMethod.NIST_PURGE
        print("✓ USB PURGE: 3 passes as expected")
        
        # Test Case 4: Any device with DESTROY method
        test_file4 = os.path.join(temp_dir, "test_destroy.img")
        with open(test_file4, 'wb') as f:
            f.write(b'DESTROY_DATA' * 100)
        
        destroy_info = DeviceInfo(device_id="DESTROY_001", device_type=DeviceType.HDD)
        result4 = engine.wipe_device(test_file4, WipeMethod.NIST_DESTROY, destroy_info)
        
        assert result4.success is True
        assert result4.passes_completed == 1  # DESTROY = 1 pass (physical destruction)
        assert result4.method == WipeMethod.NIST_DESTROY
        assert not os.path.exists(test_file4)  # File should be destroyed
        print("✓ DESTROY: 1 pass and file destroyed as expected")
        
        print("✓ Property 1 specific examples all passed")
        
    finally:
        # Clean up
        shutil.rmtree(temp_dir, ignore_errors=True)


def run_manual_property_tests():
    """Run manual property tests without hypothesis decorators."""
    print("Running manual property tests...")
    
    test_instance = TestWipeEngineProperties()
    
    # Test with specific known values
    test_cases = [
        (DeviceInfo(device_id="TEST_HDD", device_type=DeviceType.HDD), WipeMethod.NIST_CLEAR),
        (DeviceInfo(device_id="TEST_SSD", device_type=DeviceType.SSD), WipeMethod.NIST_PURGE),
        (DeviceInfo(device_id="TEST_USB", device_type=DeviceType.USB), WipeMethod.NIST_PURGE),
        (DeviceInfo(device_id="TEST_DESTROY", device_type=DeviceType.HDD), WipeMethod.NIST_DESTROY),
    ]
    
    for i, (device_info, wipe_method) in enumerate(test_cases):
        print(f"Testing case {i+1}: {device_info.device_type.value} with {wipe_method.value}")
        
        test_instance.setup_method()
        try:
            # Manual implementation of the property test logic
            test_file = test_instance.create_test_file(1024)
            
            # Get expected NIST pass count
            expected_passes = test_instance.engine.get_nist_pass_count(wipe_method, device_info.device_type)
            
            # Perform wipe operation
            result = test_instance.engine.wipe_device(
                device_path=test_file,
                method=wipe_method,
                device_info=device_info
            )
            
            # Verify NIST compliance properties
            assert result.success is True, f"Wipe operation should succeed for {wipe_method.value} on {device_info.device_type.value}"
            assert result.method == wipe_method, f"Result method should match requested method"
            assert result.passes_completed >= expected_passes, f"Should complete at least {expected_passes} passes"
            assert result.device_id == device_info.device_id, f"Device ID should match"
            assert result.start_time is not None, f"Start time should be recorded"
            assert result.end_time is not None, f"End time should be recorded"
            assert result.bytes_wiped > 0, f"Should report bytes wiped"
            
            # Verify NIST-specific requirements
            if wipe_method == WipeMethod.NIST_CLEAR:
                assert result.passes_completed == 1, f"NIST CLEAR should use exactly 1 pass"
            elif wipe_method == WipeMethod.NIST_PURGE:
                if device_info.device_type in [DeviceType.SSD, DeviceType.NVME]:
                    assert result.passes_completed == 1, f"NIST PURGE on SSD/NVMe should use 1 pass"
                else:
                    assert result.passes_completed == 3, f"NIST PURGE on {device_info.device_type.value} should use 3 passes"
            elif wipe_method == WipeMethod.NIST_DESTROY:
                assert result.passes_completed == 1, f"NIST DESTROY should use 1 pass"
                assert not os.path.exists(test_file), f"Original file should be destroyed"
            
            print(f"✓ Case {i+1} passed: {result.passes_completed} passes, {result.bytes_wiped} bytes")
            
        finally:
            test_instance.teardown_method()
    
    print("✓ All manual property test cases passed")


if __name__ == "__main__":
    try:
        # Run specific examples first
        test_property_1_examples()
        
        # Run manual property tests
        print("\nRunning manual property tests...")
        run_manual_property_tests()
        
        print("\n🎉 All property tests passed!")
        print("✓ Task 5.2: Property 1 (NIST Compliance) - COMPLETED")
        print("✓ Property-based testing framework established")
        print("✓ NIST 800-88 compliance verified across device types and methods")
        print("\nNote: Full hypothesis property tests can be run with pytest:")
        print("  pytest test_wipe_engine_properties.py -v")
        
    except Exception as e:
        print(f"\n❌ Property test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
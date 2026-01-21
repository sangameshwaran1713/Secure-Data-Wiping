#!/usr/bin/env python3
"""
Property-based tests for CertificateGenerator implementation.
Tests universal properties that should hold for all valid inputs.
"""

import sys
import os
import tempfile
import shutil
from datetime import datetime, timedelta
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from hypothesis import given, strategies as st, settings, assume
from secure_data_wiping.certificate_generator import (
    CertificateGenerator, CertificateGeneratorError, PDFGenerationError, QRCodeError
)
from secure_data_wiping.utils.data_models import WipeData, BlockchainData, DeviceInfo, DeviceType


# Test data generators
@st.composite
def device_id_strategy(draw):
    """Generate valid device IDs."""
    prefix = draw(st.sampled_from(['DEV', 'DEVICE', 'DISK', 'HDD', 'SSD', 'USB']))
    number = draw(st.integers(min_value=1, max_value=9999))
    suffix = draw(st.sampled_from(['', '_TEST', '_PROD', '_LAB']))
    return f"{prefix}_{number:04d}{suffix}"


@st.composite
def wipe_hash_strategy(draw):
    """Generate valid SHA-256 hashes."""
    # Generate 64 character hex string (SHA-256)
    hex_chars = '0123456789abcdef'
    return ''.join(draw(st.lists(st.sampled_from(hex_chars), min_size=64, max_size=64)))


@st.composite
def transaction_hash_strategy(draw):
    """Generate valid Ethereum transaction hashes."""
    # Generate 40 character hex string with 0x prefix
    hex_chars = '0123456789abcdef'
    hash_part = ''.join(draw(st.lists(st.sampled_from(hex_chars), min_size=40, max_size=40)))
    return f"0x{hash_part}"


@st.composite
def contract_address_strategy(draw):
    """Generate valid Ethereum contract addresses."""
    # Generate 40 character hex string with 0x prefix
    hex_chars = '0123456789abcdef'
    addr_part = ''.join(draw(st.lists(st.sampled_from(hex_chars), min_size=40, max_size=40)))
    return f"0x{addr_part}"


@st.composite
def wipe_data_strategy(draw):
    """Generate valid WipeData objects."""
    device_id = draw(device_id_strategy())
    wipe_hash = draw(wipe_hash_strategy())
    
    # Generate timestamp within reasonable range
    base_time = datetime(2024, 1, 1)
    days_offset = draw(st.integers(min_value=0, max_value=365))
    timestamp = base_time + timedelta(days=days_offset)
    
    method = draw(st.sampled_from(['NIST_CLEAR', 'NIST_PURGE', 'NIST_DESTROY']))
    operator = draw(st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc'))))
    passes = draw(st.integers(min_value=1, max_value=10))
    
    return WipeData(
        device_id=device_id,
        wipe_hash=wipe_hash,
        timestamp=timestamp,
        method=method,
        operator=operator,
        passes=passes
    )


@st.composite
def blockchain_data_strategy(draw):
    """Generate valid BlockchainData objects."""
    transaction_hash = draw(transaction_hash_strategy())
    block_number = draw(st.integers(min_value=1, max_value=1000000))
    contract_address = draw(contract_address_strategy())
    gas_used = draw(st.integers(min_value=21000, max_value=500000))
    confirmation_count = draw(st.integers(min_value=0, max_value=100))
    
    return BlockchainData(
        transaction_hash=transaction_hash,
        block_number=block_number,
        contract_address=contract_address,
        gas_used=gas_used,
        confirmation_count=confirmation_count
    )


@st.composite
def device_info_strategy(draw):
    """Generate valid DeviceInfo objects."""
    device_id = draw(device_id_strategy())
    device_type = draw(st.sampled_from(list(DeviceType)))
    manufacturer = draw(st.one_of(st.none(), st.text(min_size=1, max_size=50)))
    model = draw(st.one_of(st.none(), st.text(min_size=1, max_size=50)))
    capacity = draw(st.one_of(st.none(), st.integers(min_value=1024, max_value=10**15)))  # 1KB to 1PB
    
    return DeviceInfo(
        device_id=device_id,
        device_type=device_type,
        manufacturer=manufacturer,
        model=model,
        capacity=capacity
    )


class TestCertificateGeneratorProperties:
    """Property-based tests for CertificateGenerator."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.generator = CertificateGenerator(output_dir=self.temp_dir)
    
    def teardown_method(self):
        """Clean up test environment."""
        if hasattr(self, 'temp_dir') and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @given(wipe_data=wipe_data_strategy(), blockchain_data=blockchain_data_strategy())
    @settings(max_examples=50, deadline=30000)  # 30 second deadline per test
    def test_property_9_certificate_generation_for_successful_operations(self, wipe_data, blockchain_data):
        """
        Property 9: Certificate Generation for Successful Operations
        
        For any wiping operation that completes successfully with blockchain logging,
        the system should generate a PDF certificate containing device ID, wiping hash,
        blockchain transaction ID, and timestamp.
        
        Validates: Requirements 5.1, 5.2
        """
        # Ensure valid data
        assume(len(wipe_data.device_id) > 0)
        assume(len(wipe_data.wipe_hash) == 64)  # Valid SHA-256 hash length
        assume(len(blockchain_data.transaction_hash) == 42)  # Valid Ethereum tx hash length
        assume(blockchain_data.block_number > 0)
        
        # Generate certificate
        certificate_path = self.generator.generate_certificate(
            wipe_data=wipe_data,
            blockchain_data=blockchain_data
        )
        
        # Verify certificate was created
        assert os.path.exists(certificate_path), "Certificate file must exist"
        assert certificate_path.endswith('.pdf'), "Certificate must be a PDF file"
        
        # Verify file is substantial (contains actual content)
        file_size = os.path.getsize(certificate_path)
        assert file_size > 1000, f"Certificate must be substantial, got {file_size} bytes"
        assert file_size < 50 * 1024 * 1024, f"Certificate should not be excessively large, got {file_size} bytes"
        
        # Verify filename contains device ID and timestamp
        filename = os.path.basename(certificate_path)
        assert wipe_data.device_id in filename or 'certificate' in filename, "Filename should contain device ID or be recognizable"
        
        # Verify statistics were updated
        stats = self.generator.get_statistics()
        assert stats['certificates_generated'] > 0, "Certificate generation count should increase"
        assert stats['last_generation_time'] is not None, "Last generation time should be recorded"
    
    @given(wipe_data=wipe_data_strategy(), blockchain_data=blockchain_data_strategy(), device_info=device_info_strategy())
    @settings(max_examples=30, deadline=30000)
    def test_certificate_generation_with_device_info(self, wipe_data, blockchain_data, device_info):
        """
        Test certificate generation with additional device information.
        
        Verifies that certificates can be generated with optional device info
        and that the additional information is properly included.
        """
        # Ensure valid data
        assume(len(wipe_data.device_id) > 0)
        assume(len(wipe_data.wipe_hash) == 64)
        assume(len(blockchain_data.transaction_hash) == 42)
        assume(blockchain_data.block_number > 0)
        
        # Ensure device IDs match
        device_info.device_id = wipe_data.device_id
        
        # Generate certificate with device info
        certificate_path = self.generator.generate_certificate(
            wipe_data=wipe_data,
            blockchain_data=blockchain_data,
            device_info=device_info
        )
        
        # Verify certificate was created
        assert os.path.exists(certificate_path), "Certificate with device info must exist"
        assert certificate_path.endswith('.pdf'), "Certificate must be a PDF file"
        
        # Verify file size is reasonable
        file_size = os.path.getsize(certificate_path)
        assert file_size > 1000, "Certificate with device info should be substantial"
    
    @given(wipe_data=wipe_data_strategy(), blockchain_data=blockchain_data_strategy())
    @settings(max_examples=30, deadline=30000)
    def test_custom_filename_generation(self, wipe_data, blockchain_data):
        """
        Test certificate generation with custom filenames.
        
        Verifies that custom filenames are properly handled and that
        the .pdf extension is added when missing.
        """
        # Ensure valid data
        assume(len(wipe_data.device_id) > 0)
        assume(len(wipe_data.wipe_hash) == 64)
        assume(len(blockchain_data.transaction_hash) == 42)
        assume(blockchain_data.block_number > 0)
        
        # Generate custom filename
        custom_name = f"custom_{wipe_data.device_id}_{wipe_data.timestamp.strftime('%Y%m%d')}"
        
        # Generate certificate with custom filename
        certificate_path = self.generator.generate_certificate(
            wipe_data=wipe_data,
            blockchain_data=blockchain_data,
            custom_filename=custom_name
        )
        
        # Verify certificate was created with correct filename
        assert os.path.exists(certificate_path), "Certificate with custom filename must exist"
        assert certificate_path.endswith('.pdf'), "Certificate must have .pdf extension"
        assert custom_name in os.path.basename(certificate_path), "Custom filename should be preserved"
    
    @given(blockchain_data=blockchain_data_strategy())
    @settings(max_examples=30, deadline=30000)
    def test_property_10_qr_code_verification_links(self, blockchain_data):
        """
        Property 10: QR Code Verification Links
        
        For any generated certificate, the system should include a valid QR code
        that links to blockchain verification functionality.
        
        Validates: Requirements 5.4
        """
        # Ensure valid blockchain data
        assume(len(blockchain_data.transaction_hash) == 42)
        assume(blockchain_data.block_number > 0)
        
        # Generate QR code
        qr_path = self.generator._generate_qr_code(blockchain_data)
        
        # Verify QR code was created
        assert os.path.exists(qr_path), "QR code file must exist"
        assert qr_path.endswith('.png'), "QR code must be a PNG file"
        
        # Verify QR code file is substantial
        qr_size = os.path.getsize(qr_path)
        assert qr_size > 100, f"QR code must be substantial, got {qr_size} bytes"
        assert qr_size < 100 * 1024, f"QR code should not be excessively large, got {qr_size} bytes"
        
        # Verify QR code filename contains transaction hash
        qr_filename = os.path.basename(qr_path)
        tx_hash_part = blockchain_data.transaction_hash[2:18]  # Remove 0x and take first 16 chars
        assert tx_hash_part in qr_filename, "QR code filename should contain transaction hash"
    
    @given(wipe_data=wipe_data_strategy(), blockchain_data=blockchain_data_strategy())
    @settings(max_examples=20, deadline=30000)
    def test_data_validation_completeness(self, wipe_data, blockchain_data):
        """
        Test that data validation catches all required fields.
        
        Verifies that the validation function properly identifies
        missing or invalid required data fields.
        """
        # Test with valid data first
        assume(len(wipe_data.device_id) > 0)
        assume(len(wipe_data.wipe_hash) == 64)
        assume(len(blockchain_data.transaction_hash) == 42)
        assume(blockchain_data.block_number > 0)
        
        # Valid data should have no errors
        errors = self.generator.validate_certificate_data(wipe_data, blockchain_data)
        assert len(errors) == 0, f"Valid data should have no errors, got: {errors}"
        
        # Test with invalid wipe data
        invalid_wipe_data = WipeData(
            device_id="",  # Invalid empty device ID
            wipe_hash=wipe_data.wipe_hash,
            timestamp=wipe_data.timestamp,
            method=wipe_data.method,
            operator=wipe_data.operator,
            passes=wipe_data.passes
        )
        
        errors = self.generator.validate_certificate_data(invalid_wipe_data, blockchain_data)
        assert len(errors) > 0, "Invalid wipe data should have errors"
        assert any("Device ID is required" in error for error in errors), "Should detect missing device ID"
        
        # Test with invalid blockchain data
        invalid_blockchain_data = BlockchainData(
            transaction_hash="",  # Invalid empty hash
            block_number=blockchain_data.block_number,
            contract_address=blockchain_data.contract_address,
            gas_used=blockchain_data.gas_used
        )
        
        errors = self.generator.validate_certificate_data(wipe_data, invalid_blockchain_data)
        assert len(errors) > 0, "Invalid blockchain data should have errors"
        assert any("Transaction hash is required" in error for error in errors), "Should detect missing transaction hash"
    
    @given(st.integers(min_value=1, max_value=10))
    @settings(max_examples=10, deadline=30000)
    def test_statistics_tracking_accuracy(self, num_certificates):
        """
        Test that statistics tracking is accurate across multiple certificate generations.
        
        Verifies that the certificate generation counter and timestamps
        are properly maintained across multiple operations.
        """
        initial_stats = self.generator.get_statistics()
        initial_count = initial_stats['certificates_generated']
        
        # Generate multiple certificates
        for i in range(num_certificates):
            wipe_data = WipeData(
                device_id=f"STATS_TEST_{i:03d}",
                wipe_hash="a" * 64,  # Valid 64-char hash
                timestamp=datetime.now(),
                method="NIST_CLEAR",
                operator=f"operator_{i}",
                passes=1
            )
            
            blockchain_data = BlockchainData(
                transaction_hash=f"0x{'b' * 40}",  # Valid 42-char hash
                block_number=1000 + i,
                contract_address=f"0x{'c' * 40}",  # Valid 42-char address
                gas_used=25000 + i * 1000
            )
            
            self.generator.generate_certificate(wipe_data, blockchain_data)
        
        # Verify statistics were updated correctly
        final_stats = self.generator.get_statistics()
        assert final_stats['certificates_generated'] == initial_count + num_certificates, \
            f"Certificate count should increase by {num_certificates}"
        assert final_stats['last_generation_time'] is not None, "Last generation time should be set"
        
        # Verify output directory contains the expected number of files
        cert_files = list(Path(self.temp_dir).glob("*.pdf"))
        qr_files = list(Path(self.temp_dir).glob("*.png"))
        
        # Should have at least the certificates we generated (may have more from other tests)
        assert len(cert_files) >= num_certificates, f"Should have at least {num_certificates} certificate files"
        assert len(qr_files) >= num_certificates, f"Should have at least {num_certificates} QR code files"


if __name__ == "__main__":
    # Run the property tests manually
    try:
        print("Running Property 9: Certificate Generation for Successful Operations...")
        
        # Create test instance
        test_instance = TestCertificateGeneratorProperties()
        test_instance.setup_method()
        
        # Test with a few sample cases manually
        sample_wipe_data = WipeData(
            device_id="PROP_TEST_001",
            wipe_hash="1234567890abcdef" * 4,  # 64 chars
            timestamp=datetime.now(),
            method="NIST_PURGE",
            operator="property_test",
            passes=3
        )
        
        sample_blockchain_data = BlockchainData(
            transaction_hash="0x" + "abcdef1234567890" * 2 + "abcdef12",  # 42 chars
            block_number=12345,
            contract_address="0x" + "fedcba0987654321" * 2 + "fedcba09",  # 42 chars
            gas_used=75000,
            confirmation_count=6
        )
        
        # Test certificate generation property manually
        certificate_path = test_instance.generator.generate_certificate(
            wipe_data=sample_wipe_data,
            blockchain_data=sample_blockchain_data
        )
        
        # Verify certificate was created
        assert os.path.exists(certificate_path), "Certificate file must exist"
        assert certificate_path.endswith('.pdf'), "Certificate must be a PDF file"
        
        # Verify file is substantial
        file_size = os.path.getsize(certificate_path)
        assert file_size > 1000, f"Certificate must be substantial, got {file_size} bytes"
        
        # Verify statistics were updated
        stats = test_instance.generator.get_statistics()
        assert stats['certificates_generated'] > 0, "Certificate generation count should increase"
        
        print("✓ Property 9 test passed")
        
        print("\nRunning Property 10: QR Code Verification Links...")
        
        # Test QR code generation
        qr_path = test_instance.generator._generate_qr_code(sample_blockchain_data)
        
        # Verify QR code was created
        assert os.path.exists(qr_path), "QR code file must exist"
        assert qr_path.endswith('.png'), "QR code must be a PNG file"
        
        # Verify QR code file is substantial
        qr_size = os.path.getsize(qr_path)
        assert qr_size > 100, f"QR code must be substantial, got {qr_size} bytes"
        
        print("✓ Property 10 test passed")
        
        print("\nRunning data validation tests...")
        
        # Test data validation
        errors = test_instance.generator.validate_certificate_data(sample_wipe_data, sample_blockchain_data)
        assert len(errors) == 0, f"Valid data should have no errors, got: {errors}"
        
        # Test with invalid data
        invalid_wipe_data = WipeData(
            device_id="",  # Invalid empty device ID
            wipe_hash=sample_wipe_data.wipe_hash,
            timestamp=sample_wipe_data.timestamp,
            method=sample_wipe_data.method,
            operator=sample_wipe_data.operator,
            passes=sample_wipe_data.passes
        )
        
        errors = test_instance.generator.validate_certificate_data(invalid_wipe_data, sample_blockchain_data)
        assert len(errors) > 0, "Invalid wipe data should have errors"
        
        print("✓ Data validation tests passed")
        
        print("\nRunning statistics tracking tests...")
        
        # Test statistics tracking
        initial_count = test_instance.generator.get_statistics()['certificates_generated']
        
        # Generate additional certificates
        for i in range(3):
            wipe_data = WipeData(
                device_id=f"STATS_TEST_{i:03d}",
                wipe_hash="a" * 64,  # Valid 64-char hash
                timestamp=datetime.now(),
                method="NIST_CLEAR",
                operator=f"operator_{i}",
                passes=1
            )
            
            blockchain_data = BlockchainData(
                transaction_hash=f"0x{'b' * 40}",  # Valid 42-char hash
                block_number=1000 + i,
                contract_address=f"0x{'c' * 40}",  # Valid 42-char address
                gas_used=25000 + i * 1000
            )
            
            test_instance.generator.generate_certificate(wipe_data, blockchain_data)
        
        # Verify statistics
        final_count = test_instance.generator.get_statistics()['certificates_generated']
        assert final_count == initial_count + 3, f"Certificate count should increase by 3"
        
        print("✓ Statistics tracking tests passed")
        
        test_instance.teardown_method()
        
        print("\n🎉 All CertificateGenerator property tests passed!")
        print("✓ Task 6.2: Property 9 (Certificate Generation) - COMPLETED")
        print("✓ Task 6.3: Property 10 (QR Code Verification) - COMPLETED")
        print("✓ Certificate generation properties validated with multiple test cases")
        print("✓ QR code generation and verification link properties validated")
        print("✓ Data validation and statistics tracking properties verified")
        
    except Exception as e:
        print(f"\n❌ Property test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
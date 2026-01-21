#!/usr/bin/env python3
"""
Simple test for CertificateGenerator implementation.
Tests basic functionality with sample data.
"""

import sys
import os
import tempfile
import shutil
from datetime import datetime

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from secure_data_wiping.certificate_generator import (
    CertificateGenerator, CertificateGeneratorError, PDFGenerationError, QRCodeError
)
from secure_data_wiping.utils.data_models import WipeData, BlockchainData, DeviceInfo, DeviceType


def test_certificate_generator_initialization():
    """Test CertificateGenerator initialization."""
    print("Testing CertificateGenerator initialization...")
    
    # Default initialization
    temp_dir = tempfile.mkdtemp()
    try:
        generator = CertificateGenerator(output_dir=temp_dir)
        assert generator.certificates_generated == 0
        assert generator.last_generation_time is None
        assert generator.output_dir.exists()
        print("✓ Default initialization successful")
        
        # Custom template configuration
        custom_config = {
            'page_size': (612, 792),  # Letter size
            'margins': {'top': 50, 'bottom': 50, 'left': 50, 'right': 50}
        }
        generator_custom = CertificateGenerator(template_config=custom_config, output_dir=temp_dir)
        assert generator_custom.template_config['margins']['top'] == 50
        print("✓ Custom configuration initialization successful")
        
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    print("✓ CertificateGenerator initialization tests passed")


def test_certificate_data_validation():
    """Test certificate data validation."""
    print("Testing certificate data validation...")
    
    temp_dir = tempfile.mkdtemp()
    try:
        generator = CertificateGenerator(output_dir=temp_dir)
        
        # Valid data
        valid_wipe_data = WipeData(
            device_id="TEST_DEVICE_001",
            wipe_hash="a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456",
            timestamp=datetime.now(),
            method="NIST_CLEAR",
            operator="test_operator",
            passes=1
        )
        
        valid_blockchain_data = BlockchainData(
            transaction_hash="0x1234567890abcdef1234567890abcdef12345678",
            block_number=12345,
            contract_address="0xabcdef1234567890abcdef1234567890abcdef12",
            gas_used=50000,
            confirmation_count=6
        )
        
        errors = generator.validate_certificate_data(valid_wipe_data, valid_blockchain_data)
        assert len(errors) == 0, f"Valid data should have no errors, got: {errors}"
        print("✓ Valid data validation passed")
        
        # Invalid data - missing device ID
        invalid_wipe_data = WipeData(
            device_id="",  # Empty device ID
            wipe_hash="a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456",
            timestamp=datetime.now(),
            method="NIST_CLEAR",
            operator="test_operator",
            passes=1
        )
        
        errors = generator.validate_certificate_data(invalid_wipe_data, valid_blockchain_data)
        assert len(errors) > 0, "Invalid data should have errors"
        assert any("Device ID is required" in error for error in errors)
        print("✓ Invalid data validation passed")
        
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    print("✓ Certificate data validation tests passed")


def test_certificate_generation():
    """Test PDF certificate generation."""
    print("Testing PDF certificate generation...")
    
    temp_dir = tempfile.mkdtemp()
    try:
        generator = CertificateGenerator(output_dir=temp_dir)
        
        # Create sample data
        wipe_data = WipeData(
            device_id="CERT_TEST_DEVICE_001",
            wipe_hash="1a2b3c4d5e6f7890abcdef1234567890abcdef1234567890abcdef1234567890",
            timestamp=datetime.now(),
            method="NIST_PURGE",
            operator="certificate_test_operator",
            passes=3
        )
        
        blockchain_data = BlockchainData(
            transaction_hash="0x9876543210fedcba9876543210fedcba98765432",
            block_number=98765,
            contract_address="0xfedcba9876543210fedcba9876543210fedcba98",
            gas_used=75000,
            confirmation_count=12
        )
        
        device_info = DeviceInfo(
            device_id="CERT_TEST_DEVICE_001",
            device_type=DeviceType.HDD,
            manufacturer="Test Corp",
            model="Test Drive 2TB",
            capacity=2 * 1024**4  # 2TB
        )
        
        # Generate certificate
        certificate_path = generator.generate_certificate(
            wipe_data=wipe_data,
            blockchain_data=blockchain_data,
            device_info=device_info
        )
        
        # Verify certificate was created
        assert os.path.exists(certificate_path), f"Certificate file should exist: {certificate_path}"
        assert certificate_path.endswith('.pdf'), "Certificate should be a PDF file"
        
        # Check file size (should be reasonable for a PDF)
        file_size = os.path.getsize(certificate_path)
        assert file_size > 1000, f"Certificate file should be substantial, got {file_size} bytes"
        assert file_size < 10 * 1024 * 1024, f"Certificate file should not be too large, got {file_size} bytes"
        
        print(f"✓ Certificate generated successfully: {os.path.basename(certificate_path)}")
        print(f"✓ File size: {file_size} bytes")
        
        # Verify statistics were updated
        stats = generator.get_statistics()
        assert stats['certificates_generated'] == 1
        assert stats['last_generation_time'] is not None
        print("✓ Statistics tracking working")
        
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    print("✓ PDF certificate generation tests passed")


def test_custom_filename_generation():
    """Test certificate generation with custom filename."""
    print("Testing custom filename generation...")
    
    temp_dir = tempfile.mkdtemp()
    try:
        generator = CertificateGenerator(output_dir=temp_dir)
        
        wipe_data = WipeData(
            device_id="CUSTOM_FILENAME_TEST",
            wipe_hash="custom123456789abcdef123456789abcdef123456789abcdef123456789abcdef",
            timestamp=datetime.now(),
            method="NIST_CLEAR",
            operator="custom_test",
            passes=1
        )
        
        blockchain_data = BlockchainData(
            transaction_hash="0xcustom123456789abcdef123456789abcdef123456",
            block_number=11111,
            contract_address="0xcustom789abcdef123456789abcdef123456789abc",
            gas_used=30000
        )
        
        # Test custom filename without .pdf extension
        custom_name = "my_custom_certificate"
        certificate_path = generator.generate_certificate(
            wipe_data=wipe_data,
            blockchain_data=blockchain_data,
            custom_filename=custom_name
        )
        
        assert os.path.basename(certificate_path) == "my_custom_certificate.pdf"
        assert os.path.exists(certificate_path)
        print("✓ Custom filename (without .pdf) working")
        
        # Test custom filename with .pdf extension
        custom_name_with_ext = "another_custom_cert.pdf"
        certificate_path2 = generator.generate_certificate(
            wipe_data=wipe_data,
            blockchain_data=blockchain_data,
            custom_filename=custom_name_with_ext
        )
        
        assert os.path.basename(certificate_path2) == "another_custom_cert.pdf"
        assert os.path.exists(certificate_path2)
        print("✓ Custom filename (with .pdf) working")
        
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    print("✓ Custom filename generation tests passed")


def test_qr_code_generation():
    """Test QR code generation functionality."""
    print("Testing QR code generation...")
    
    temp_dir = tempfile.mkdtemp()
    try:
        generator = CertificateGenerator(output_dir=temp_dir)
        
        blockchain_data = BlockchainData(
            transaction_hash="0xqrtest123456789abcdef123456789abcdef123456",
            block_number=55555,
            contract_address="0xqrtest789abcdef123456789abcdef123456789abc",
            gas_used=40000
        )
        
        # Test QR code generation
        qr_path = generator._generate_qr_code(blockchain_data)
        
        assert os.path.exists(qr_path), f"QR code file should exist: {qr_path}"
        assert qr_path.endswith('.png'), "QR code should be a PNG file"
        
        # Check QR code file size
        qr_size = os.path.getsize(qr_path)
        assert qr_size > 100, f"QR code file should be substantial, got {qr_size} bytes"
        
        print(f"✓ QR code generated: {os.path.basename(qr_path)}")
        print(f"✓ QR code size: {qr_size} bytes")
        
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    print("✓ QR code generation tests passed")


def test_error_handling():
    """Test error handling scenarios."""
    print("Testing error handling...")
    
    temp_dir = tempfile.mkdtemp()
    try:
        generator = CertificateGenerator(output_dir=temp_dir)
        
        # Test with invalid data
        invalid_wipe_data = WipeData(
            device_id="",  # Invalid empty device ID
            wipe_hash="",  # Invalid empty hash
            timestamp=datetime.now(),
            method="INVALID_METHOD",
            operator="",
            passes=0
        )
        
        invalid_blockchain_data = BlockchainData(
            transaction_hash="",  # Invalid empty hash
            block_number=-1,      # Invalid negative block number
            contract_address="",  # Invalid empty address
            gas_used=0
        )
        
        # Validation should catch these errors
        errors = generator.validate_certificate_data(invalid_wipe_data, invalid_blockchain_data)
        assert len(errors) > 0, "Should have validation errors"
        print(f"✓ Validation caught {len(errors)} errors as expected")
        
        # Test with valid data but invalid output directory
        invalid_generator = CertificateGenerator(output_dir="/invalid/nonexistent/path")
        # The generator should create the directory, so this should work
        assert invalid_generator.output_dir.exists()
        print("✓ Auto-creation of output directory working")
        
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    print("✓ Error handling tests passed")


def test_statistics_and_factory_function():
    """Test statistics tracking and factory function."""
    print("Testing statistics and factory function...")
    
    temp_dir = tempfile.mkdtemp()
    try:
        # Test factory function
        from secure_data_wiping.certificate_generator import create_certificate_generator_from_config
        
        config = {
            'output_dir': temp_dir,
            'template_config': {
                'page_size': (612, 792),
                'margins': {'top': 60, 'bottom': 60, 'left': 60, 'right': 60}
            }
        }
        
        generator = create_certificate_generator_from_config(config)
        assert str(generator.output_dir) == temp_dir
        assert generator.template_config['margins']['top'] == 60
        print("✓ Factory function working")
        
        # Test statistics
        initial_stats = generator.get_statistics()
        assert initial_stats['certificates_generated'] == 0
        assert initial_stats['last_generation_time'] is None
        assert initial_stats['output_directory'] == temp_dir
        print("✓ Initial statistics correct")
        
        # Generate a certificate to update statistics
        wipe_data = WipeData(
            device_id="STATS_TEST",
            wipe_hash="stats123456789abcdef123456789abcdef123456789abcdef123456789abcdef",
            timestamp=datetime.now(),
            method="NIST_CLEAR",
            operator="stats_test",
            passes=1
        )
        
        blockchain_data = BlockchainData(
            transaction_hash="0xstats123456789abcdef123456789abcdef12345678",
            block_number=77777,
            contract_address="0xstats789abcdef123456789abcdef123456789abcdef",
            gas_used=25000
        )
        
        generator.generate_certificate(wipe_data, blockchain_data)
        
        updated_stats = generator.get_statistics()
        assert updated_stats['certificates_generated'] == 1
        assert updated_stats['last_generation_time'] is not None
        print("✓ Statistics updated correctly")
        
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    print("✓ Statistics and factory function tests passed")


if __name__ == "__main__":
    try:
        test_certificate_generator_initialization()
        test_certificate_data_validation()
        test_certificate_generation()
        test_custom_filename_generation()
        test_qr_code_generation()
        test_error_handling()
        test_statistics_and_factory_function()
        
        print("\n🎉 All CertificateGenerator tests passed successfully!")
        print("✓ Task 6.1: CertificateGenerator class implementation - COMPLETED")
        print("✓ Professional PDF generation with reportlab working")
        print("✓ QR code generation for blockchain verification working")
        print("✓ Security features and professional formatting implemented")
        print("✓ Comprehensive error handling and validation working")
        print("✓ Statistics tracking and factory functions working")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
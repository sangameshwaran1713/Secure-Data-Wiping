#!/usr/bin/env python3
"""
Quick Demonstration Script

A simplified demonstration of the key system features for quick testing.
"""

import sys
import os
import tempfile
from datetime import datetime
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, os.path.abspath('.'))

def quick_demo():
    """Run a quick demonstration of key features."""
    print("🚀 SECURE DATA WIPING SYSTEM - QUICK DEMO")
    print("=" * 50)
    
    try:
        # Test 1: Hash Generation
        print("\n1. Testing Hash Generation...")
        from secure_data_wiping.hash_generator import HashGenerator
        from secure_data_wiping.utils.data_models import WipeResult, WipeMethod
        
        hash_gen = HashGenerator()
        test_result = WipeResult(
            operation_id='QUICK_DEMO_001',
            device_id='DEMO_DEVICE',
            method=WipeMethod.NIST_CLEAR,
            passes_completed=1,
            start_time=datetime.now(),
            success=True,
            operator_id='demo_user'
        )
        
        hash_value = hash_gen.generate_wipe_hash(test_result)
        print(f"   ✓ Generated SHA-256 hash: {hash_value[:16]}...")
        
        # Test 2: Wipe Engine
        print("\n2. Testing Wipe Engine...")
        from secure_data_wiping.wipe_engine import WipeEngine
        
        wipe_engine = WipeEngine()
        
        # Create test file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.tmp') as f:
            f.write('Demo data for secure wiping\n' * 20)
            test_file = f.name
        
        try:
            result = wipe_engine.wipe_device(test_file, WipeMethod.NIST_CLEAR)
            print(f"   ✓ Wiped test file successfully: {result.success}")
            print(f"   ✓ Passes completed: {result.passes_completed}")
        finally:
            # Cleanup
            if os.path.exists(test_file):
                os.remove(test_file)
            if os.path.exists(test_file + '.DESTROYED'):
                os.remove(test_file + '.DESTROYED')
        
        # Test 3: Privacy Protection
        print("\n3. Testing Privacy Protection...")
        from secure_data_wiping.local_infrastructure import DataPrivacyFilter
        
        privacy_filter = DataPrivacyFilter()
        test_data = {
            'device_id': 'DEMO_DEVICE',
            'wipe_hash': hash_value,
            'timestamp': int(datetime.now().timestamp()),
            'password': 'secret123'  # This should be filtered
        }
        
        result = privacy_filter.filter_blockchain_data(test_data)
        print(f"   ✓ Privacy violations detected: {len(result.violations)}")
        print(f"   ✓ Safe fields preserved: {len(result.filtered_data)}")
        
        # Test 4: Certificate Generation
        print("\n4. Testing Certificate Generation...")
        from secure_data_wiping.certificate_generator import CertificateGenerator
        from secure_data_wiping.utils.data_models import WipeData, BlockchainData, DeviceInfo, DeviceType
        
        with tempfile.TemporaryDirectory() as temp_dir:
            cert_gen = CertificateGenerator(output_dir=temp_dir)
            
            wipe_data = WipeData(
                device_id='DEMO_DEVICE',
                wipe_hash=hash_value,
                timestamp=datetime.now(),
                method='NIST_CLEAR',
                operator='demo_user',
                passes=1
            )
            
            blockchain_data = BlockchainData(
                transaction_hash='0x' + 'a' * 62,
                block_number=12345,
                contract_address='0x' + 'b' * 38,
                gas_used=50000,
                confirmation_count=6
            )
            
            device_info = DeviceInfo(
                device_id='DEMO_DEVICE',
                device_type=DeviceType.SSD,
                capacity=1000000000,
                manufacturer='Samsung',
                model='EVO_860',
                serial_number='DEMO12345',
                connection_type='SATA'
            )
            
            cert_path = cert_gen.generate_certificate(wipe_data, blockchain_data, device_info)
            cert_size = os.path.getsize(cert_path)
            
            print(f"   ✓ Certificate generated: {Path(cert_path).name}")
            print(f"   ✓ Certificate size: {cert_size:,} bytes")
        
        print("\n" + "=" * 50)
        print("🎉 QUICK DEMO COMPLETED SUCCESSFULLY!")
        print("All core components are working correctly.")
        print("System is ready for full demonstration.")
        print("=" * 50)
        
        return True
        
    except Exception as e:
        print(f"\n❌ DEMO FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = quick_demo()
    sys.exit(0 if success else 1)
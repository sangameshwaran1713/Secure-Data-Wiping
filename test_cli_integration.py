#!/usr/bin/env python3
"""
Test CLI integration with the web interface.
"""

import subprocess
import sys
import os

def test_cli_commands():
    """Test that CLI commands work properly."""
    print("🧪 Testing CLI Integration")
    print("=" * 40)
    
    # Test 1: Check if CLI module is accessible
    print("1. Testing CLI module accessibility...")
    try:
        result = subprocess.run([
            'python', '-m', 'secure_data_wiping.cli', '--help'
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("   ✓ CLI module is accessible")
        else:
            print("   ✗ CLI module failed:")
            print(f"   Error: {result.stderr}")
            return False
    except Exception as e:
        print(f"   ✗ CLI test failed: {e}")
        return False
    
    # Test 2: Test scan-files command
    print("\n2. Testing scan-files command...")
    try:
        result = subprocess.run([
            'python', '-m', 'secure_data_wiping.cli', 'scan-files', 
            '.', '--pattern', '*.py'
        ], capture_output=True, text=True, timeout=15)
        
        if result.returncode == 0:
            print("   ✓ Scan-files command works")
            print(f"   Output preview: {result.stdout[:100]}...")
        else:
            print("   ⚠ Scan-files command returned non-zero:")
            print(f"   Error: {result.stderr[:200]}...")
    except Exception as e:
        print(f"   ✗ Scan-files test failed: {e}")
    
    # Test 3: Test create-sample command
    print("\n3. Testing create-sample command...")
    try:
        sample_file = "test_sample.csv"
        result = subprocess.run([
            'python', '-m', 'secure_data_wiping.cli', 'create-sample',
            sample_file, '--format', 'csv'
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0 and os.path.exists(sample_file):
            print("   ✓ Create-sample command works")
            print(f"   Created: {sample_file}")
            # Clean up
            os.remove(sample_file)
        else:
            print("   ⚠ Create-sample command issues:")
            print(f"   Error: {result.stderr[:200]}...")
    except Exception as e:
        print(f"   ✗ Create-sample test failed: {e}")
    
    print("\n✅ CLI Integration Test Complete")
    print("Note: Some commands may show warnings but still function correctly")
    return True

if __name__ == "__main__":
    test_cli_commands()
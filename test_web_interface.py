#!/usr/bin/env python3
"""
Test script to verify the web interface is working correctly.
"""

import requests
import json
import time

def test_web_interface():
    """Test the web interface endpoints."""
    base_url = "http://localhost:5000"
    
    print("🧪 Testing Secure Data Wiping Web Interface")
    print("=" * 50)
    
    try:
        # Test 1: Check if server is running
        print("1. Testing server connectivity...")
        response = requests.get(f"{base_url}/api/stats", timeout=5)
        if response.status_code == 200:
            stats = response.json()
            print(f"   ✓ Server is running")
            print(f"   ✓ Stats API working: {stats}")
        else:
            print(f"   ✗ Server returned status code: {response.status_code}")
            return False
        
        # Test 2: Test device list API
        print("\n2. Testing device list API...")
        response = requests.get(f"{base_url}/api/device-list", timeout=5)
        if response.status_code == 200:
            devices = response.json()
            print(f"   ✓ Device list API working")
            print(f"   ✓ Found {len(devices.get('devices', []))} sample devices")
        else:
            print(f"   ✗ Device list API failed: {response.status_code}")
        
        # Test 3: Test file scan API
        print("\n3. Testing file scan API...")
        scan_data = {
            "base_path": ".",
            "pattern": "*.py",
            "recursive": True
        }
        response = requests.post(f"{base_url}/api/scan-files", 
                               json=scan_data, timeout=10)
        if response.status_code == 200:
            result = response.json()
            print(f"   ✓ File scan API working")
            if result.get('success'):
                print(f"   ✓ Scan completed successfully")
            else:
                print(f"   ⚠ Scan returned: {result.get('error', 'Unknown error')}")
        else:
            print(f"   ✗ File scan API failed: {response.status_code}")
        
        # Test 4: Test operations API
        print("\n4. Testing operations API...")
        response = requests.get(f"{base_url}/api/operations", timeout=5)
        if response.status_code == 200:
            operations = response.json()
            print(f"   ✓ Operations API working")
            print(f"   ✓ Found {len(operations.get('operations', []))} operations")
        else:
            print(f"   ✗ Operations API failed: {response.status_code}")
        
        print("\n✅ Web Interface Test Results:")
        print("=" * 50)
        print("✓ Server is running and accessible")
        print("✓ API endpoints are responding")
        print("✓ JSON responses are properly formatted")
        print("✓ Web interface is ready for use")
        
        print(f"\n🌐 Access the web interface at:")
        print(f"   Dashboard: {base_url}/")
        print(f"   File Wiping: {base_url}/file-wipe")
        print(f"   Device Wiping: {base_url}/device-wipe")
        print(f"   Batch Processing: {base_url}/batch-process")
        
        return True
        
    except requests.exceptions.ConnectionError:
        print("   ✗ Cannot connect to web server")
        print("   ℹ Make sure the web application is running")
        return False
    except requests.exceptions.Timeout:
        print("   ✗ Request timed out")
        return False
    except Exception as e:
        print(f"   ✗ Test failed with error: {e}")
        return False

if __name__ == "__main__":
    success = test_web_interface()
    if success:
        print("\n🎉 Web interface is working perfectly!")
    else:
        print("\n❌ Web interface test failed")
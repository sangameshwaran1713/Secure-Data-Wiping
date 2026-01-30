#!/usr/bin/env python3
"""
Test script for batch processing API endpoints
"""

import requests
import json

def test_batch_upload():
    """Test the batch upload endpoint"""
    print("Testing batch upload API...")
    
    # Create test CSV content
    csv_content = """device_id,device_type,manufacturer,model,serial_number,capacity,wipe_method,passes
DEV_001,hdd,Seagate,ST1000DM003,ABC123,1TB,purge,3
DEV_002,ssd,Samsung,850 EVO,XYZ789,512GB,clear,1"""
    
    # Save to temporary file
    with open('test_devices.csv', 'w') as f:
        f.write(csv_content)
    
    # Test upload
    try:
        with open('test_devices.csv', 'rb') as f:
            files = {'file': ('test_devices.csv', f, 'text/csv')}
            response = requests.post('http://localhost:5000/api/batch-upload', files=files)
            
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print(f"✅ Upload successful! Found {data.get('count')} devices")
                return data.get('devices', [])
            else:
                print(f"❌ Upload failed: {data.get('error')}")
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    return []

def test_batch_process(devices):
    """Test the batch processing endpoint"""
    if not devices:
        print("No devices to process")
        return
        
    print("Testing batch processing API...")
    
    try:
        payload = {
            'devices': devices,
            'config': {
                'continue_on_error': True,
                'generate_report': True,
                'parallel_processing': False,
                'max_concurrent': 1,
                'timeout': 30
            }
        }
        
        response = requests.post(
            'http://localhost:5000/api/batch-process',
            json=payload,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                stats = data.get('statistics', {})
                print(f"✅ Batch processing successful!")
                print(f"   Total: {stats.get('total', 0)}")
                print(f"   Successful: {stats.get('successful', 0)}")
                print(f"   Failed: {stats.get('failed', 0)}")
                print(f"   Success Rate: {stats.get('success_rate', 0):.1f}%")
            else:
                print(f"❌ Batch processing failed: {data.get('error')}")
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

def test_server_connection():
    """Test if server is running"""
    try:
        response = requests.get('http://localhost:5000/api/stats', timeout=5)
        print(f"✅ Server is running (Status: {response.status_code})")
        return True
    except Exception as e:
        print(f"❌ Server not accessible: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Batch Processing API")
    print("=" * 40)
    
    # Test server connection
    if not test_server_connection():
        print("Please start the web server first: python web_app.py")
        exit(1)
    
    # Test batch upload
    devices = test_batch_upload()
    
    # Test batch processing
    if devices:
        test_batch_process(devices)
    
    print("=" * 40)
    print("🏁 Testing completed")
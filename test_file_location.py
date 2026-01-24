#!/usr/bin/env python3
"""
Test to verify file locations and deletion behavior.
"""

import os
import requests
import json
import time

def test_file_deletion_behavior():
    """Test the actual file deletion behavior."""
    
    print("🔍 TESTING FILE DELETION BEHAVIOR")
    print("=" * 50)
    
    # Create a test file in the project directory
    original_file = "test_original_file.txt"
    with open(original_file, 'w') as f:
        f.write("This is the original test file in the project directory.")
    
    print(f"✅ Created original file: {original_file}")
    print(f"📁 Original file exists: {os.path.exists(original_file)}")
    
    # Upload the file to web interface (this creates a copy in web_uploads)
    print(f"\n📤 Uploading file to web interface...")
    
    try:
        with open(original_file, 'rb') as f:
            files = {'file': (original_file, f, 'text/plain')}
            response = requests.post('http://localhost:5000/api/upload', files=files)
        
        if response.status_code == 200:
            result = response.json()
            uploaded_path = result.get('file_path', '')
            print(f"✅ File uploaded successfully")
            print(f"📁 Uploaded file path: {uploaded_path}")
            print(f"📁 Uploaded file exists: {os.path.exists(uploaded_path)}")
            
            # Now delete the uploaded file via web interface
            print(f"\n🗑️ Deleting uploaded file via web interface...")
            
            delete_data = {
                "file_path": uploaded_path,
                "method": "clear",
                "passes": 1,
                "verify": True,
                "wipe_metadata": True
            }
            
            delete_response = requests.post(
                'http://localhost:5000/api/wipe-file',
                json=delete_data,
                timeout=30
            )
            
            if delete_response.status_code == 200:
                delete_result = delete_response.json()
                print(f"📋 Deletion result: {'SUCCESS' if delete_result.get('success') else 'FAILED'}")
                
                time.sleep(1)
                
                # Check both files
                print(f"\n📊 RESULTS:")
                print(f"📁 Original file ({original_file}): {'EXISTS' if os.path.exists(original_file) else 'DELETED'}")
                print(f"📁 Uploaded copy ({uploaded_path}): {'EXISTS' if os.path.exists(uploaded_path) else 'DELETED'}")
                
                print(f"\n💡 EXPLANATION:")
                print(f"   • The web interface only deletes the UPLOADED COPY in web_uploads/")
                print(f"   • Your ORIGINAL FILE remains untouched in its original location")
                print(f"   • This is the expected behavior for security reasons")
                
            else:
                print(f"❌ Deletion failed: {delete_response.status_code}")
        else:
            print(f"❌ Upload failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Clean up
    if os.path.exists(original_file):
        os.remove(original_file)
        print(f"\n🧹 Cleaned up original test file")

if __name__ == "__main__":
    test_file_deletion_behavior()
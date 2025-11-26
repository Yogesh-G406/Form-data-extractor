"""
Quick Test Script for Langfuse Integration
Run this to verify that Langfuse is tracking events correctly
"""

import requests
import json
import time

# Configuration
BASE_URL = "http://localhost:8001"
TEST_IMAGE = r"C:\Users\Aseuro\Downloads\img6.jpg"

print("=" * 60)
print("🧪 Testing Langfuse Integration")
print("=" * 60)

# Test 1: Health Check
print("\n1️⃣ Testing Health Check...")
try:
    response = requests.get(f"{BASE_URL}/health")
    health = response.json()
    print(f"   ✅ Backend is healthy")
    print(f"   📊 Langfuse configured: {health.get('langfuse_configured', False)}")
    print(f"   🤖 Agent initialized: {health.get('agent_initialized', False)}")
except Exception as e:
    print(f"   ❌ Error: {e}")
    exit(1)

# Test 2: Upload File
print("\n2️⃣ Testing File Upload (this will create Langfuse events)...")
try:
    with open(TEST_IMAGE, 'rb') as f:
        files = {'file': (TEST_IMAGE.split('\\')[-1], f, 'image/jpeg')}
        response = requests.post(
            f"{BASE_URL}/upload",
            files=files,
            params={'language': 'English'}
        )
    
    if response.status_code == 200:
        result = response.json()
        print(f"   ✅ Upload successful!")
        print(f"   📄 Filename: {result.get('filename')}")
        print(f"   💾 Saved to DB: {result.get('saved_to_database')}")
        print(f"   🆔 Form ID: {result.get('form_id')}")
        print(f"   📊 Fields extracted: {len(result.get('extracted_data', {}))}")
    else:
        print(f"   ⚠️  Upload failed with status {response.status_code}")
        print(f"   Error: {response.text}")
except FileNotFoundError:
    print(f"   ⚠️  Test image not found at: {TEST_IMAGE}")
    print(f"   💡 Update TEST_IMAGE path in this script")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 3: Get Forms
print("\n3️⃣ Testing Get Forms (CRUD operation tracking)...")
try:
    response = requests.get(f"{BASE_URL}/forms")
    forms = response.json()
    print(f"   ✅ Retrieved {len(forms)} forms from database")
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n" + "=" * 60)
print("✅ Testing Complete!")
print("=" * 60)
print("\n📊 Check your Langfuse Dashboard:")
print("   🔗 https://cloud.langfuse.com")
print("\n🔍 Look for these events:")
print("   • api_request_POST_/upload (trace)")
print("   • file_upload (event)")
print("   • handwriting_extraction (trace with generation)")
print("   • form_created (event)")
print("   • api_request_GET_/forms (trace)")
print("\n⏱️  Events may take a few seconds to appear in Langfuse")
print("=" * 60)

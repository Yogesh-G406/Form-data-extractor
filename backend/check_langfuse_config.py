"""
Check Langfuse Configuration
"""
import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
env_path = Path('.env')
load_dotenv(env_path)

print("=" * 60)
print("🔍 Langfuse Configuration Check")
print("=" * 60)

public_key = os.getenv("LANGFUSE_PUBLIC_KEY", "NOT SET")
secret_key = os.getenv("LANGFUSE_SECRET_KEY", "NOT SET")
host = os.getenv("LANGFUSE_HOST", "NOT SET")

print(f"\n📋 Configuration:")
print(f"   Public Key: {public_key}")
print(f"   Secret Key: {secret_key[:20]}..." if secret_key != "NOT SET" else "   Secret Key: NOT SET")
print(f"   Host: {host}")

print(f"\n✅ Expected Configuration:")
print(f"   Public Key: pk-lf-b09e2b78-8241-45e7-a591-a01d1502e2dd")
print(f"   Secret Key: sk-lf-e25ec2f8-c0f8-4afe-aa10-1cf846143a08")
print(f"   Host: https://cloud.langfuse.com")

print(f"\n🎯 Project Info:")
print(f"   Project Name: Yogesh")
print(f"   Project ID: cmie6a4m70059ad07l8pas71c")
print(f"   Region: EU")

# Check if configuration matches
if public_key == "pk-lf-b09e2b78-8241-45e7-a591-a01d1502e2dd":
    print(f"\n✅ Public key matches!")
else:
    print(f"\n❌ Public key does NOT match!")
    
if secret_key == "sk-lf-e25ec2f8-c0f8-4afe-aa10-1cf846143a08":
    print(f"✅ Secret key matches!")
else:
    print(f"❌ Secret key does NOT match!")
    
if host == "https://cloud.langfuse.com":
    print(f"✅ Host is correct!")
else:
    print(f"❌ Host is incorrect! Should be: https://cloud.langfuse.com")

print("\n" + "=" * 60)

# Now test if Langfuse client can be initialized
print("\n🧪 Testing Langfuse Client Initialization...")
try:
    from langfuse import Langfuse
    
    client = Langfuse(
        public_key=public_key,
        secret_key=secret_key,
        host=host
    )
    
    print("✅ Langfuse client initialized successfully!")
    
    # Try to create a test event
    print("\n📤 Sending test event...")
    client.event(
        name="test_event_from_script",
        metadata={
            "test": True,
            "source": "configuration_check",
            "project": "Yogesh"
        }
    )
    
    client.flush()
    print("✅ Test event sent!")
    print("\n🔍 Check your Langfuse dashboard:")
    print("   1. Go to: https://cloud.langfuse.com")
    print("   2. Click 'Events' in the sidebar")
    print("   3. Look for: 'test_event_from_script'")
    print("   4. Wait 10-30 seconds and refresh")
    
except Exception as e:
    print(f"❌ Error: {e}")
    print("\nPossible issues:")
    print("   - API keys are incorrect")
    print("   - Network connectivity problem")
    print("   - Langfuse service is down")

print("\n" + "=" * 60)

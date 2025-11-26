
import os
import time
from dotenv import load_dotenv
from langfuse import Langfuse
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("langfuse_test")

# Load env
load_dotenv()

print("="*60)
print("DIAGNOSING LOCAL LANGFUSE CONFIGURATION")
print("="*60)

public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
secret_key = os.getenv("LANGFUSE_SECRET_KEY")
host = os.getenv("LANGFUSE_HOST")

print(f"Host: {host}")
print(f"Public Key: {public_key}")
print(f"Secret Key: {secret_key[:10]}..." if secret_key else "None")

try:
    # Initialize client
    print("\n1. Initializing Client...")
    langfuse = Langfuse(
        public_key=public_key,
        secret_key=secret_key,
        host=host
    )
    print("   Client initialized")

    # Test Trace
    print("\n2. Sending Test Trace...")
    trace = langfuse.trace(
        name="diagnostic_test_trace",
        metadata={"env": "local", "test": "true"}
    )
    print("   Trace created object")
    
    # Test Generation
    print("\n3. Adding Generation...")
    generation = trace.generation(
        name="diagnostic_generation",
        model="test-model",
        input="test input",
        metadata={"foo": "bar"}
    )
    print("   Generation added")
    
    # Update Generation
    generation.update(output="test output")
    print("   Generation updated")
    
    # Flush
    print("\n4. Flushing to Server...")
    start = time.time()
    langfuse.flush()
    duration = time.time() - start
    print(f"   Flushed in {duration:.2f}s")
    
    print("\nSUCCESS! Data sent to Langfuse.")
    print(f"Check your local dashboard at {host}")
    print("Look for trace named 'diagnostic_test_trace'")

except Exception as e:
    print(f"\nERROR: {e}")
    import traceback
    traceback.print_exc()
    
    print("\nTROUBLESHOOTING:")
    if "Connection refused" in str(e):
        print("   - Is Langfuse Docker running?")
        print("   - Can you open http://localhost:3000 in browser?")
    elif "401" in str(e) or "403" in str(e):
        print("   - Check your API Keys in .env")
    elif "AttributeError" in str(e):
        print("   - SDK Version mismatch. Please run: pip install --upgrade langfuse")

print("="*60)

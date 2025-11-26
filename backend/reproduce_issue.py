
import os
import time
from langfuse import Langfuse
from dotenv import load_dotenv

load_dotenv("backend/.env")

def reproduce():
    public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
    secret_key = os.getenv("LANGFUSE_SECRET_KEY")
    host = os.getenv("LANGFUSE_HOST")
    
    print(f"Connecting to Langfuse: {host}")
    
    langfuse = Langfuse(public_key=public_key, secret_key=secret_key, host=host)
    
    print("Creating trace...")
    trace = langfuse.trace(
        name="repro_trace",
        input={"test": "initial_input"},
        metadata={"env": "dev"}
    )
    
    print("Creating event...")
    trace.create_event(
        name="repro_event",
        input={"event_input": "some data"},
        output={"event_output": "success"}
    )
    
    print("Updating trace...")
    trace.update(
        input="Updated Input",
        output={"final": "result"}
    )
    
    print("Ending trace...")
    # trace.end() # trace() objects don't always need end() if they are not spans, but let's check SDK
    
    langfuse.flush()
    print("Done. Check Langfuse UI.")

if __name__ == "__main__":
    reproduce()

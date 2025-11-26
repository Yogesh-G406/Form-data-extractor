
import os
from langfuse import Langfuse
from dotenv import load_dotenv

load_dotenv("backend/.env")

def inspect_span():
    public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
    secret_key = os.getenv("LANGFUSE_SECRET_KEY")
    host = os.getenv("LANGFUSE_HOST")
    
    langfuse = Langfuse(public_key=public_key, secret_key=secret_key, host=host)
    
    print("Creating span...")
    span = langfuse.start_span(name="test_span")
    print("Span attributes:")
    print(dir(span))
    
    if hasattr(span, 'update'):
        print("Span has 'update' method")
    else:
        print("Span has NO 'update' method")
        
    if hasattr(span, 'event'):
        print("Span has 'event' method")
    
    if hasattr(span, 'create_event'):
        print("Span has 'create_event' method")
        
    span.end()
    langfuse.flush()

if __name__ == "__main__":
    inspect_span()


import os
from langfuse import Langfuse
from dotenv import load_dotenv

load_dotenv("backend/.env")

def test_start_generation():
    public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
    secret_key = os.getenv("LANGFUSE_SECRET_KEY")
    host = os.getenv("LANGFUSE_HOST")
    
    langfuse = Langfuse(public_key=public_key, secret_key=secret_key, host=host)
    
    print("Creating Root Span...")
    root_span = langfuse.start_span(name="root")
    
    if hasattr(root_span, 'start_generation'):
        print("Root Span has 'start_generation'")
        try:
            gen = root_span.start_generation(name="gen")
            print("Successfully created generation using start_generation")
            gen.end()
        except Exception as e:
            print(f"Failed start_generation: {e}")
            
    if hasattr(root_span, 'generation'):
        print("Root Span has 'generation'")
    else:
        print("Root Span does NOT have 'generation'")

    root_span.end()
    langfuse.flush()

if __name__ == "__main__":
    test_start_generation()

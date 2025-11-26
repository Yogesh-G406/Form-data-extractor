
import os
from langfuse import Langfuse
from dotenv import load_dotenv

load_dotenv("backend/.env")

def inspect_span_attributes():
    public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
    secret_key = os.getenv("LANGFUSE_SECRET_KEY")
    host = os.getenv("LANGFUSE_HOST")
    
    langfuse = Langfuse(public_key=public_key, secret_key=secret_key, host=host)
    
    span = langfuse.start_span(name="test_span")
    print("LangfuseSpan attributes:")
    print(dir(span))
    span.end()

if __name__ == "__main__":
    inspect_span_attributes()

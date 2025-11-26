
import os
import time
from langfuse import Langfuse
from dotenv import load_dotenv

load_dotenv("backend/.env")

def test_full_flow():
    public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
    secret_key = os.getenv("LANGFUSE_SECRET_KEY")
    host = os.getenv("LANGFUSE_HOST")
    
    print(f"Connecting to Langfuse: {host}")
    langfuse = Langfuse(public_key=public_key, secret_key=secret_key, host=host)
    
    print("1. Starting Root Span (mimicking main.py)...")
    # Mimic main.py root_trace
    root_span = langfuse.start_span(
        name="test_root_span",
        input={"filename": "test.jpg"},
        metadata={"env": "test"}
    )
    
    print("2. Starting Child Span (mimicking agent.py)...")
    # Mimic agent.py extract_handwriting
    child_span = root_span.start_span(
        name="test_child_span",
        input="OCR Prompt",
        metadata={"model": "test-model"}
    )
    
    print("3. Creating Generation (mimicking agent.py)...")
    # Mimic agent.py generation
    generation = child_span.generation(
        name="test_generation",
        model="test-model-v1",
        input="OCR Prompt Content",
        metadata={"provider": "test"}
    )
    
    # Simulate LLM call
    time.sleep(1)
    output_text = '{"field": "value"}'
    
    print("4. Updating Generation...")
    generation.update(
        output=output_text,
        usage={"input": 10, "output": 5}
    )
    generation.end()
    
    print("5. Updating Child Span...")
    child_span.update(
        output={"extracted": "data"},
        metadata={"duration": 1.0}
    )
    child_span.end()
    
    print("6. Updating Root Span...")
    root_span.update(
        input="Final Prompt",
        output={"final": "result"}
    )
    root_span.end()
    
    langfuse.flush()
    print("Done. Check Langfuse UI for 'test_root_span'.")

if __name__ == "__main__":
    test_full_flow()

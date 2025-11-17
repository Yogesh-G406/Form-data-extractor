from fastapi import FastAPI

# Create the FastAPI app instance (must be named 'app')
app = FastAPI()

# Example endpoint
@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI!"}

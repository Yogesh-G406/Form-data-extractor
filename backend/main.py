import os
import json
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from sqlalchemy import select
from agent import HandwritingExtractionAgent
from database import get_db, FormData

# Load .env file from the backend directory
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".pdf"}
MAX_FILE_SIZE = 10 * 1024 * 1024

agent = None

class FormDataCreate(BaseModel):
    form_name: str
    data: str

class FormDataUpdate(BaseModel):
    form_name: str = None
    data: str = None

class FormDataResponse(BaseModel):
    id: int
    form_name: str
    data: str
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global agent
    try:
        agent = HandwritingExtractionAgent()
        print("[OK] Handwriting Extraction Agent initialized")
    except Exception as e:
        print(f"[WARNING] Agent initialization failed: {e}")
        print("Please ensure Ollama is running and reachable (see README)")
    yield
    # Shutdown (if needed)
    pass

app = FastAPI(
    title="Handwriting Extraction API",
    description="AI-powered handwritten text extraction using Ollama (vision model) and Langfuse",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "message": "Handwriting Extraction API",
        "version": "1.0.0",
        "endpoints": {
            "/upload": "POST - Upload handwritten image for extraction",
            "/health": "GET - Health check",
            "/forms": "GET - Get all form data",
            "/forms": "POST - Create new form data",
            "/forms/{id}": "GET - Get form data by ID",
            "/forms/{id}": "PUT - Update form data",
            "/forms/{id}": "DELETE - Delete form data"
        }
    }

@app.get("/health")
async def health_check():
    ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    ollama_model = os.getenv("OLLAMA_MODEL", "llava")
    backend=os.getenv("VITE_API_URL", "http://localhost:8000")
    return {
        "status": "healthy",
        "agent_initialized": agent is not None,
        "ollama_host": ollama_host,
        "ollama_model": ollama_model,
        "backend_url": backend,
        "langfuse_configured": bool(os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY"))
    }

@app.post("/upload")
async def upload_file(file: UploadFile = File(...), language: str = "English", db: Session = Depends(get_db)):
    if not agent:
        raise HTTPException(
            status_code=503,
            detail="Agent not initialized. Please ensure the Ollama service is running."
        )
    
    filename = file.filename or "unknown.jpg"
    file_ext = Path(filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type {file_ext} not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    if file_ext == ".pdf":
        raise HTTPException(
            status_code=400,
            detail="PDF processing requires additional setup with poppler-utils. Please upload JPG or PNG images."
        )
    
    file_path = None
    try:
        contents = await file.read()
        
        if len(contents) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File size exceeds maximum allowed size of {MAX_FILE_SIZE / (1024*1024)}MB"
            )
        
        file_path = UPLOAD_DIR / filename
        with open(file_path, "wb") as f:
            f.write(contents)
        
        result = agent.extract_handwriting(str(file_path), filename, language)
        
        try:
            os.remove(file_path)
        except Exception as e:
            print(f"[WARNING] Failed to delete temporary file: {e}")
        
        if result["success"]:
            try:
                db_form = FormData(
                    form_name=filename,
                    data=json.dumps(result["extracted_data"])
                )
                db.add(db_form)
                db.commit()
                db.refresh(db_form)
                
                formatted_result = {
                    "success": result["success"],
                    "filename": result["filename"],
                    "message": result["message"],
                    "extracted_data": result["extracted_data"],
                    "form_id": db_form.id,
                    "saved_to_database": True
                }
            except Exception as db_error:
                db.rollback()
                print(f"[WARNING] Failed to save to database: {db_error}")
                formatted_result = {
                    "success": result["success"],
                    "filename": result["filename"],
                    "message": result["message"],
                    "extracted_data": result["extracted_data"],
                    "saved_to_database": False
                }
            
            return JSONResponse(
                content=formatted_result,
                media_type="application/json"
            )
        else:
            raise HTTPException(status_code=500, detail=result.get("error", "Extraction failed"))
            
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_details = str(e)
        error_type = type(e).__name__
        print(f"[ERROR] Upload error: {error_type}: {error_details}")
        print(f"[ERROR] Traceback: {traceback.format_exc()}")
        
        if file_path and file_path.exists():
            try:
                os.remove(file_path)
            except:
                pass
        
        raise HTTPException(
            status_code=500,
            detail=f"Error processing file: {error_type}: {error_details}"
        )

@app.post("/forms", response_model=FormDataResponse)
async def create_form(form_data: FormDataCreate, db: Session = Depends(get_db)):
    try:
        db_form = FormData(form_name=form_data.form_name, data=form_data.data)
        db.add(db_form)
        db.commit()
        db.refresh(db_form)
        return {
            "id": db_form.id,
            "form_name": db_form.form_name,
            "data": db_form.data,
            "created_at": db_form.created_at.isoformat(),
            "updated_at": db_form.updated_at.isoformat()
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

def serialize_form(form: FormData):
    return {
        "id": form.id,
        "form_name": form.form_name,
        "data": form.data,
        "created_at": form.created_at.isoformat(),
        "updated_at": form.updated_at.isoformat()
    }

@app.get("/forms")
async def get_all_forms(db: Session = Depends(get_db)):
    try:
        stmt = select(FormData)
        forms = db.execute(stmt).scalars().all()
        return [serialize_form(form) for form in forms]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/forms/{form_id}", response_model=FormDataResponse)
async def get_form(form_id: int, db: Session = Depends(get_db)):
    try:
        stmt = select(FormData).where(FormData.id == form_id)
        form = db.execute(stmt).scalar_one_or_none()
        if not form:
            raise HTTPException(status_code=404, detail=f"Form with id {form_id} not found")
        return serialize_form(form)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/forms/{form_id}", response_model=FormDataResponse)
async def update_form(form_id: int, form_data: FormDataUpdate, db: Session = Depends(get_db)):
    try:
        stmt = select(FormData).where(FormData.id == form_id)
        form = db.execute(stmt).scalar_one_or_none()
        if not form:
            raise HTTPException(status_code=404, detail=f"Form with id {form_id} not found")
        
        if form_data.form_name is not None:
            form.form_name = form_data.form_name
        if form_data.data is not None:
            form.data = form_data.data
        
        db.commit()
        db.refresh(form)
        return serialize_form(form)
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/forms/{form_id}")
async def delete_form(form_id: int, db: Session = Depends(get_db)):
    try:
        stmt = select(FormData).where(FormData.id == form_id)
        form = db.execute(stmt).scalar_one_or_none()
        if not form:
            raise HTTPException(status_code=404, detail=f"Form with id {form_id} not found")
        
        db.delete(form)
        db.commit()
        return {"message": f"Form with id {form_id} deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
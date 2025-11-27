import os
import json
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from sqlalchemy import select
from langfuse import Langfuse
from agent import HandwritingExtractionAgent
from langchain_agent import LangChainFormAgent
from database import get_db, FormData
from langfuse_middleware import LangfuseMiddleware

# Load .env file from the backend directory
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".pdf"}
MAX_FILE_SIZE = 10 * 1024 * 1024

agent = None
langchain_agent = None
langfuse_client = None

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
    
    model_config = ConfigDict(from_attributes=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global agent, langchain_agent, langfuse_client
    
    # Initialize Langfuse
    langfuse_public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
    langfuse_secret_key = os.getenv("LANGFUSE_SECRET_KEY")
    langfuse_host = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
    
    if langfuse_public_key and langfuse_secret_key:
        try:
            langfuse_client = Langfuse(
                public_key=langfuse_public_key,
                secret_key=langfuse_secret_key,
                host=langfuse_host
            )
            print(f"[DEBUG] Langfuse client initialized with host: {langfuse_host}")
        except Exception as e:
            print(f"[WARNING] Failed to initialize Langfuse client: {e}")
    else:
        print("[WARNING] Langfuse credentials not configured")
    
    try:
        agent = HandwritingExtractionAgent()
        print("[OK] Handwriting Extraction Agent initialized")
    except Exception as e:
        print(f"[WARNING] Agent initialization failed: {e}")
        print("Please ensure Ollama is running and reachable (see README)")
    
    try:
        langchain_agent = LangChainFormAgent()
        print("[OK] LangChain Form Agent initialized")
    except Exception as e:
        print(f"[WARNING] LangChain Form Agent initialization failed: {e}")
        print("Form field extraction via LangChain will not be available")
    
    yield
    # Shutdown
    if langfuse_client:
        langfuse_client.flush()
        print("[OK] Langfuse client flushed")

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

# Add Langfuse middleware
if langfuse_client:
    app.add_middleware(LangfuseMiddleware, langfuse_client=langfuse_client)

@app.get("/")
async def root():
    return {
        "message": "Handwriting Extraction API",
        "version": "1.0.0",
        "endpoints": {
            "/upload": "POST - Upload handwritten image for extraction",
            "/health": "GET - Health check",
            "/extract-form-fields": "POST - Extract and structure form fields from text",
            "/validate-form": "POST - Validate extracted form fields",
            "/classify-form": "POST - Classify form type",
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
        "langchain_agent_initialized": langchain_agent is not None,
        "ollama_host": ollama_host,
        "ollama_model": ollama_model,
        "backend_url": backend,
        "langfuse_configured": bool(os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY"))
    }

class ExtractFormFieldsRequest(BaseModel):
    extracted_text: dict
    language: str = "English"

class ValidateFormRequest(BaseModel):
    fields: list
    expected_fields: list = None

class ClassifyFormRequest(BaseModel):
    extracted_text: dict

@app.post("/extract-form-fields")
async def extract_form_fields(request: ExtractFormFieldsRequest):
    if not langchain_agent:
        raise HTTPException(
            status_code=503,
            detail="LangChain Form Agent not initialized. Check HuggingFace token configuration."
        )
    
    try:
        result = langchain_agent.extract_form_fields(
            request.extracted_text,
            request.language
        )
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/validate-form")
async def validate_form(request: ValidateFormRequest):
    if not langchain_agent:
        raise HTTPException(
            status_code=503,
            detail="LangChain Form Agent not initialized."
        )
    
    try:
        result = langchain_agent.validate_form_fields(
            request.fields,
            request.expected_fields
        )
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/classify-form")
async def classify_form(request: ClassifyFormRequest):
    if not langchain_agent:
        raise HTTPException(
            status_code=503,
            detail="LangChain Form Agent not initialized."
        )
    
    try:
        result = langchain_agent.classify_form(request.extracted_text)
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
        file_size = len(contents)
        
        # Track file upload event (Root Trace)
        root_trace = None
        if langfuse_client:
            print("[DEBUG] Attempting to create root trace...")
            try:
                # Create a root trace for the entire request
                if hasattr(langfuse_client, 'trace'):
                    root_trace = langfuse_client.trace(
                        name="file_upload_request",
                        input={"filename": filename, "file_type": file_ext, "size": file_size},
                        metadata={
                            "filename": filename,
                            "file_type": file_ext,
                            "file_size_bytes": file_size,
                            "language": language
                        }
                    )
                elif hasattr(langfuse_client, 'start_span'):
                    root_trace = langfuse_client.start_span(
                        name="file_upload_request",
                        input={"filename": filename, "file_type": file_ext, "size": file_size},
                        metadata={
                            "filename": filename,
                            "file_type": file_ext,
                            "file_size_bytes": file_size,
                            "language": language
                        }
                    )
            except Exception as lf_error:
                print(f"[WARNING] Langfuse tracking failed: {lf_error}")
        
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File size exceeds maximum allowed size of {MAX_FILE_SIZE / (1024*1024)}MB"
            )
        
        file_path = UPLOAD_DIR / filename
        with open(file_path, "wb") as f:
            f.write(contents)
        
        # Extract handwriting using agent, passing the root trace
        result = agent.extract_handwriting(str(file_path), filename, language, parent_trace=root_trace)
        
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
                
                # Track database save event
                if root_trace:
                    try:
                        root_trace.create_event(
                            name="form_created",
                            input={"filename": filename, "extracted_data": result["extracted_data"]},
                            output={"success": True, "form_id": db_form.id},
                            metadata={
                                "form_id": db_form.id,
                                "form_name": filename,
                                "fields_count": len(result["extracted_data"])
                            }
                        )
                    except Exception as lf_error:
                        print(f"[WARNING] Langfuse tracking failed: {lf_error}")
                
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
                
                # Track database error
                if root_trace:
                    try:
                        root_trace.create_event(
                            name="database_error",
                            input={"operation": "create_form", "filename": filename},
                            output={"error": str(db_error)},
                            metadata={
                                "operation": "create_form",
                                "error": str(db_error)
                            }
                        )
                    except Exception as lf_error:
                        print(f"[WARNING] Langfuse tracking failed: {lf_error}")
                
                formatted_result = {
                    "success": result["success"],
                    "filename": result["filename"],
                    "message": result["message"],
                    "extracted_data": result["extracted_data"],
                    "saved_to_database": False
                }

            # Update and end root trace with success info
            if root_trace:
                try:
                    # Get prompt and extracted data from result
                    prompt = result.get("prompt", "Prompt not available")
                    extracted_data = result.get("extracted_data", {})
                    
                    root_trace.update(
                        input=prompt, 
                        output=extracted_data
                    )
                    root_trace.end()
                except Exception as lf_error:
                    print(f"[WARNING] Langfuse trace update failed: {lf_error}")
            
            return JSONResponse(
                content=formatted_result,
                media_type="application/json"
            )
        else:
            error_msg = result.get("error", "Extraction failed")
            status_code = 503 if "not initialized" in error_msg else 500
            raise HTTPException(status_code=status_code, detail=error_msg)
            
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_details = str(e)
        error_type = type(e).__name__
        print(f"[ERROR] Upload error: {error_type}: {error_details}")
        print(f"[ERROR] Traceback: {traceback.format_exc()}")
        
        # Track upload error
        if root_trace:
            try:
                root_trace.create_event(
                    name="upload_error",
                    input={"filename": filename},
                    output={"error": error_details, "type": error_type},
                    metadata={
                        "filename": filename,
                        "error_type": error_type,
                        "error_message": error_details
                    }
                )
            except Exception as lf_error:
                print(f"[WARNING] Langfuse tracking failed: {lf_error}")
        
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
        
        # Track form creation (manual) - this is separate endpoint, keep as create_event
        if langfuse_client:
            try:
                langfuse_client.create_event(
                    name="form_created_manual",
                    input=form_data.model_dump(),
                    output={"success": True, "form_id": db_form.id},
                    metadata={
                        "form_id": db_form.id,
                        "form_name": form_data.form_name
                    }
                )
            except Exception as lf_error:
                print(f"[WARNING] Langfuse tracking failed: {lf_error}")
        
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
        
        # Track form update
        if langfuse_client:
            update_data = form_data.model_dump(exclude_unset=True)
            try:
                langfuse_client.create_event(
                    name="form_updated",
                    input={"form_id": form_id, "updates": update_data},
                    output={"success": True},
                    metadata={
                        "form_id": form_id,
                        "updated_fields": list(update_data.keys())
                    }
                )
            except Exception as lf_error:
                print(f"[WARNING] Langfuse tracking failed: {lf_error}")
        
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
        
        form_name = form.form_name
        db.delete(form)
        db.commit()
        
        # Track form deletion
        if langfuse_client:
            try:
                langfuse_client.create_event(
                    name="form_deleted",
                    input={"form_id": form_id},
                    output={"success": True},
                    metadata={
                        "form_id": form_id,
                        "success": True
                    }
                )
            except Exception as lf_error:
                print(f"[WARNING] Langfuse tracking failed: {lf_error}")
        
        return {"message": f"Form with id {form_id} deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
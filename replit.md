# Handwriting Extraction AI - Project Overview

## Project Description
A full-stack web application that uses AI vision technology to extract text from handwritten images. Built with FastAPI backend, React frontend, LangChain for orchestration, and Langfuse for observability.

## Recent Changes
- **2025-11-14**: Initial project creation
  - Set up FastAPI backend with file upload endpoint
  - Created LangChain agent with GPT-4 Vision integration
  - Integrated Langfuse for AI observability and tracing
  - Built React frontend with drag-and-drop upload interface
  - Configured workflows for both backend and frontend
  - Added comprehensive error handling and validation

## Architecture

### Backend (Python/FastAPI)
- **Location**: `backend/`
- **Main Files**:
  - `main.py`: FastAPI application with file upload endpoint
  - `agent.py`: LangChain agent with vision LLM and Langfuse integration
  - `requirements.txt`: Python dependencies

**Key Features**:
- File upload endpoint (`POST /upload`)
- Health check endpoint (`GET /health`)
- File validation (JPG, PNG, max 10MB)
- Temporary file storage and cleanup
- CORS configuration for frontend

### Frontend (React/Vite)
- **Location**: `frontend/`
- **Main Files**:
  - `src/App.jsx`: Main application component
  - `src/components/FileUpload.jsx`: File upload with drag-and-drop
  - `src/components/ResultDisplay.jsx`: JSON result display
  - `vite.config.js`: Vite configuration with proxy to backend

**Key Features**:
- Drag-and-drop file upload
- Image preview before processing
- Beautiful JSON display
- Copy to clipboard functionality
- Error handling and loading states

### AI Agent (LangChain)
- Uses GPT-4 Vision (gpt-4o model)
- Extracts handwritten text without predefined schema
- No hallucinations - only extracts visible content
- Langfuse integration for tracing and observability

## Environment Setup

### Required Secrets
- `OPENAI_API_KEY`: OpenAI API key for GPT-4 Vision (REQUIRED)

### Optional Secrets (for Langfuse observability)
- `LANGFUSE_PUBLIC_KEY`: Langfuse public key
- `LANGFUSE_SECRET_KEY`: Langfuse secret key
- `LANGFUSE_HOST`: Langfuse host URL (default: https://cloud.langfuse.com)

## Workflows

### Backend
- **Command**: `cd backend && python main.py`
- **Port**: 8000
- **Type**: Console (API server)

### Frontend
- **Command**: `cd frontend && npm run dev`
- **Port**: 5000
- **Type**: Webview (user interface)

## Technology Stack

### Backend
- FastAPI 0.121.2
- LangChain 1.0.5
- LangChain-OpenAI 1.0.2
- Langfuse 3.9.3
- Pillow 12.0.0
- Uvicorn 0.38.0

### Frontend
- React 18.2.0
- Vite 5.0.12
- Axios 1.6.5

## User Preferences
None specified yet. Default setup follows standard Python and React conventions.

## Next Steps
1. User needs to provide OPENAI_API_KEY via secrets
2. Optional: Add Langfuse credentials for observability
3. Test with handwritten images
4. Consider adding PDF support with poppler-utils
5. Add batch processing capabilities
6. Implement result history/database storage

"""
FastAPI Application for StudyRAG
REST API endpoints for PDF upload and Q&A
"""
import os
import shutil
from pathlib import Path
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from backend.config import (
    APP_NAME,
    APP_VERSION,
    APP_DESCRIPTION,
    UPLOAD_DIR
)
from backend.rag_pipeline import get_rag_pipeline
from backend.retrieval_service import get_retrieval_service


# Pydantic Models
class QuestionRequest(BaseModel):
    """Request model for asking questions"""
    question: str = Field(..., description="Question to ask about the document")
    k: int = Field(default=4, description="Number of documents to retrieve", ge=1, le=10)
    include_sources: bool = Field(default=True, description="Include source documents in response")


class UploadResponse(BaseModel):
    """Response model for PDF upload"""
    success: bool
    message: str
    filename: str
    vectorstore_name: str
    num_pages: Optional[int] = None
    num_chunks: Optional[int] = None


class QuestionResponse(BaseModel):
    """Response model for Q&A"""
    question: str
    answer: str
    model: str
    sources: Optional[List[Dict[str, Any]]] = None
    num_sources: Optional[int] = None


# Initialize FastAPI app
app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description=APP_DESCRIPTION
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Initialize services
rag_pipeline = get_rag_pipeline()
retrieval_service = get_retrieval_service()


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": APP_NAME,
        "version": APP_VERSION,
        "description": APP_DESCRIPTION,
        "endpoints": {
            "upload": "/upload - Upload PDF and create vector store",
            "ask": "/ask - Ask questions about uploaded document",
            "docs": "/docs - Interactive API documentation"
        }
    }


@app.post("/upload", response_model=UploadResponse)
async def upload_pdf(
    file: UploadFile = File(..., description="PDF file to upload"),
    vectorstore_name: str = Form(default="default", description="Name for the vector store")
):
    """
    Upload a PDF file and create a vector store
    
    - **file**: PDF file to process
    - **vectorstore_name**: Optional name for the vector store (default: "default")
    """
    # Validate file type
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    try:
        # Save uploaded file
        file_path = Path(UPLOAD_DIR) / file.filename
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        print(f"\n📤 Uploaded file: {file.filename}")
        
        # Process PDF with RAG pipeline
        vectorstore = rag_pipeline.process_pdf(str(file_path), vectorstore_name)
        
        # Get document count
        num_chunks = vectorstore.index.ntotal if vectorstore else 0
        
        return UploadResponse(
            success=True,
            message=f"PDF processed successfully. Vector store '{vectorstore_name}' created.",
            filename=file.filename,
            vectorstore_name=vectorstore_name,
            num_chunks=num_chunks
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")


@app.post("/ask", response_model=QuestionResponse)
async def ask_question(request: QuestionRequest):
    """
    Ask a question about the uploaded document
    
    - **question**: Your question
    - **k**: Number of relevant documents to retrieve (1-10)
    - **include_sources**: Whether to include source documents
    """
    try:
        # Check if vectorstore is loaded
        if rag_pipeline.vectorstore is None:
            raise HTTPException(
                status_code=400,
                detail="No document loaded. Please upload a PDF first using /upload endpoint."
            )
        
        # Get answer from retrieval service
        result = retrieval_service.ask(
            question=request.question,
            k=request.k,
            include_sources=request.include_sources
        )
        
        return QuestionResponse(**result)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error answering question: {str(e)}")


@app.post("/load-vectorstore")
async def load_existing_vectorstore(vectorstore_name: str = Form(default="default")):
    """
    Load an existing vector store
    
    - **vectorstore_name**: Name of the vector store to load
    """
    try:
        retrieval_service.load_vectorstore(vectorstore_name)
        return {
            "success": True,
            "message": f"Vector store '{vectorstore_name}' loaded successfully"
        }
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"Vector store '{vectorstore_name}' not found"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading vector store: {str(e)}")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "vectorstore_loaded": rag_pipeline.vectorstore is not None
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

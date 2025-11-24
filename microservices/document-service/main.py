from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import FastAPI, BackgroundTasks, HTTPException, status, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import shutil
import uuid
from pathlib import Path
import json
from enum import Enum

# Import required classes from fastapi and other modules
from fastapi import FastAPI, Depends, BackgroundTasks
import uvicorn

# Pydantic models
class DocumentStatus(str, Enum):
    UPLOADED = "UPLOADED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    ERROR = "ERROR"
    CANCELLED = "CANCELLED"

class DocumentResponse(BaseModel):
    id: str
    filename: str
    original_filename: str
    file_path: str
    file_size: int
    mime_type: str
    status: str
    owner_id: int
    created_at: datetime
    updated_at: datetime
    processed_at: Optional[datetime] = None

class KeyFigure(BaseModel):
    name: str
    value: str
    source_page: Optional[int] = None
    source_section: Optional[str] = None

class DocumentAnalysisResponse(BaseModel):
    summary: str
    key_figures: List[KeyFigure]
    vector_db_path: str

class QuestionRequest(BaseModel):
    question: str

class SourceReference(BaseModel):
    page: Optional[int] = None
    snippet: Optional[str] = None
    section: Optional[str] = None

class QuestionResponse(BaseModel):
    answer: str
    sources: List[SourceReference]

class StatusUpdateRequest(BaseModel):
    status: str

# Initialize FastAPI app
app = FastAPI(
    title="Document Processing Service",
    version="1.0.0",
    root_path="/documents"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
STORAGE_PATH = os.getenv("STORAGE_PATH", "/data/storage")
TEMP_DIR = os.path.join(STORAGE_PATH, "temp")
os.makedirs(TEMP_DIR, exist_ok=True)

def process_document_background(document_id: str):
    """Background task to process the document"""
    print(f"Processing document {document_id} in background...")
    pass

@app.get("/")
def read_root():
    return {"service": "document-service", "status": "running"}

@app.post("/", response_model=DocumentResponse)
def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    owner_id: int = 1  # This would come from authentication in a real implementation
):
    # Validate file type
    allowed_types = [
        'application/pdf',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/msword',
        'text/plain',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    ]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"File type {file.content_type} not allowed. Allowed types: {', '.join(allowed_types)}"
        )

    # Generate unique filename
    unique_filename = f"{str(uuid.uuid4())}_{file.filename}"
    file_path = os.path.join(TEMP_DIR, unique_filename)

    # Save file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Get file size
    file_size = os.path.getsize(file_path)
    
    # Create document record
    document_record = DocumentResponse(
        id=str(uuid.uuid4()),
        filename=unique_filename,
        original_filename=file.filename,
        file_path=file_path,
        file_size=file_size,
        mime_type=file.content_type,
        status="UPLOADED",
        owner_id=owner_id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    # Process document in background
    # background_tasks.add_task(process_document_background, document_record.id)
    
    return document_record

@app.get("/{document_id}", response_model=DocumentResponse)
def get_document(document_id: str):
    # In a real implementation, this would fetch from database
    # For now, return a mock document
    return DocumentResponse(
        id=document_id,
        filename=f"document_{document_id}.pdf",
        original_filename=f"original_document_{document_id}.pdf",
        file_path=f"/data/temp/document_{document_id}.pdf",
        file_size=1024000,
        mime_type="application/pdf",
        status="COMPLETED",
        owner_id=1,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        processed_at=datetime.utcnow()
    )

@app.delete("/{document_id}")
def delete_document(document_id: str):
    # In a real implementation, this would delete the document from storage and DB
    # For now, just return success message
    return {"message": f"Document {document_id} deleted successfully"}

@app.get("/{document_id}/analysis", response_model=DocumentAnalysisResponse)
def get_document_analysis(document_id: str):
    # In a real implementation, this would fetch from database
    # For now, return mock analysis
    return DocumentAnalysisResponse(
        summary="This is a mock financial document summary. In a real implementation, this would contain AI-generated insights from processing the financial document.",
        key_figures=[
            KeyFigure(name="Total Revenue", value="$1.25B", source_page=12),
            KeyFigure(name="Net Income", value="$187M", source_page=15),
            KeyFigure(name="Operating Margin", value="18.3%", source_page=18),
            KeyFigure(name="EPS", value="$3.42", source_page=22)
        ],
        vector_db_path=f"/vector_dbs/{document_id}.faiss"
    )

@app.post("/{document_id}/ask", response_model=QuestionResponse)
def ask_question(document_id: str, request: QuestionRequest):
    # In a real implementation, this would connect to the LLM service
    # For now, return mock Q&A response
    question_lower = request.question.lower()
    
    if "revenue" in question_lower:
        answer = "The total revenue for this fiscal year was $1.25 billion, representing a growth of 12.5% compared to the previous year. This growth was primarily driven by strong performance in the core business units and new market expansion."
        sources = [
            SourceReference(page=12, snippet="Revenue increased to $1.25B from $1.1B in the previous year"),
            SourceReference(page=15, snippet="Strong growth in core business segments contributed to the 12.5% increase")
        ]
    elif "profit" in question_lower or "income" in question_lower:
        answer = "The net income for this period was $187 million with an earnings per share (EPS) of $3.42. This reflects improved operational efficiency and cost management initiatives."
        sources = [
            SourceReference(page=18, snippet="Net income recorded at $187M for the fiscal year"),
            SourceReference(page=22, snippet="EPS reported as $3.42, up from $3.15 in previous year")
        ]
    else:
        answer = "Based on the financial document, the company demonstrates solid fundamentals with revenue growth of 12.5%, improved operating margins of 18.3% (up from 16.7%), and a conservative debt-to-equity ratio of 0.68. The strategic outlook remains positive."
        sources = [
            SourceReference(page=12, snippet="Revenue grew by 12.5% year-over-year"),
            SourceReference(page=15, snippet="Operating margins improved to 18.3% from 16.7% in previous year"),
            SourceReference(page=48, snippet="Debt-to-equity ratio of 0.68 indicates conservative capital structure")
        ]
    
    return QuestionResponse(answer=answer, sources=sources)

@app.patch("/{document_id}/status")
def update_document_status(document_id: str, request: StatusUpdateRequest):
    # In a real implementation, this would update the document status in the database
    # For now, just return success
    return {"message": f"Document {document_id} status updated to {request.status}"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "document-service"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)
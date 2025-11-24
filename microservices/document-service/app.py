from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
import os
import uuid
import tempfile
import shutil
from datetime import datetime
import hashlib
import logging

from models import Document, Base
from schemas import DocumentResponse, DocumentCreate, DocumentUpdate, QuestionResponse, QuestionRequest
from config import SessionLocal, engine, get_db
from utils import (
    get_file_size,
    generate_unique_filename,
    ensure_directory_exists,
    calculate_file_hash,
    format_file_size,
    validate_file_type
)

# Create database tables
Base.metadata.create_all(bind=engine)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Document Processing Service",
    version="1.0.0",
    root_path="/documents"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def process_document(document_id: int):
    """Background task to process document."""
    # Get a fresh database session for background task
    db = SessionLocal()
    try:
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            logger.error(f"Document {document_id} not found for processing")
            return
            
        # Update status to processing
        document.status = "PROCESSING"
        document.updated_at = datetime.utcnow()
        db.commit()
        
        # In a real implementation, this is where we would:
        # 1. Extract text from PDF using PyMuPDF
        # 2. Chunk the document using LangChain
        # 3. Create embeddings using FAISS
        # 4. Perform analysis with LLM
        # 5. Store results in vector DB
        # For now, we'll simulate processing
        import time
        time.sleep(2)  # Simulate processing time
        
        # Update status to completed
        document.status = "COMPLETED"
        document.processed_at = datetime.utcnow()
        document.updated_at = datetime.utcnow()
        db.commit()
        
        logger.info(f"Document {document_id} processed successfully")
    except Exception as e:
        logger.error(f"Error processing document {document_id}: {e}")
        # Update status to error
        document = db.query(Document).filter(Document.id == document_id).first()
        if document:
            document.status = "ERROR"
            document.updated_at = datetime.utcnow()
            db.commit()
    finally:
        db.close()

@app.get("/")
def read_root():
    return {"service": "document-service", "status": "running"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "document-service"}

@app.get("/{document_id}", response_model=DocumentResponse)
def get_document(document_id: int, db: Session = Depends(get_db)):
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document

@app.get("/", response_model=List[DocumentResponse])
def get_documents(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    documents = db.query(Document).offset(skip).limit(limit).all()
    return documents

@app.post("/", response_model=DocumentResponse)
def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    # Validate file type
    allowed_extensions = ['.pdf', '.txt', '.docx', '.xlsx', '.csv']
    if not validate_file_type(file.filename or "", allowed_extensions):
        raise HTTPException(
            status_code=400,
            detail=f"File type not allowed. Allowed types: {', '.join(allowed_extensions)}"
        )
    
    # Create unique filename
    unique_filename = generate_unique_filename(file.filename or "unnamed.pdf")
    file_path = os.path.join("/data", "temp", unique_filename)
    
    # Ensure directory exists
    ensure_directory_exists(os.path.dirname(file_path))
    
    # Save file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Calculate file size
    file_size = get_file_size(file_path)
    
    # Create document record
    db_document = Document(
        filename=unique_filename,
        original_filename=file.filename or "unnamed.pdf",
        file_path=file_path,
        file_size=file_size,
        mime_type=file.content_type,
        status="UPLOADED",
        owner_id=1  # This would come from authentication in real implementation
    )
    
    db.add(db_document)
    db.commit()
    db.refresh(db_document)
    
    # Process document in background
    background_tasks.add_task(process_document, db_document.id)
    
    return db_document

@app.patch("/{document_id}", response_model=DocumentResponse)
def update_document(
    document_id: int,
    document_update: DocumentUpdate,
    db: Session = Depends(get_db)
):
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    if document_update.status:
        document.status = document_update.status
        document.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(document)
    return document

@app.delete("/{document_id}")
def delete_document(document_id: int, db: Session = Depends(get_db)):
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Delete file if it exists
    if os.path.exists(document.file_path):
        try:
            os.remove(document.file_path)
            logger.info(f"Deleted file: {document.file_path}")
        except Exception as e:
            logger.error(f"Error deleting file: {e}")
    
    # Delete document record
    db.delete(document)
    db.commit()
    
    return {"message": "Document deleted successfully"}
"""
Refactored backend service for the AI Financial Analyst application.
Main FastAPI application with routes and endpoints.
"""

import os
import io
import json
import shutil
import logging
from datetime import datetime
from typing import List, Dict, Any

# FastAPI imports
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, BackgroundTasks, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session

# Local imports
from models import Base, User, Document, AnalysisResult, QASession, Question
from schemas import (
    UserCreate, UserResponse, Token, DocumentResponse, AnalysisResultResponse,
    QuestionRequest, QuestionResponse, LLMStatusResponse, LLMModeRequest
)
from config import engine, SessionLocal, STORAGE_PATH, DOCUMENTS_BUCKET, minio_client
from auth import get_db, get_current_user
from utils import (
    authenticate_user, create_user, get_user_by_email, get_document_by_id,
    get_analysis_result, create_qa_session, create_question,
    delete_document_and_related_data
)
from background_tasks import process_document_task
from llm_integration import (
    ask_question, get_llm_status, set_llm_mode, get_available_llm_modes
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create database tables
Base.metadata.create_all(bind=engine)
logger.info("Database tables created successfully")

# FastAPI app
app = FastAPI(title="AI Financial Analyst API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
@app.post("/token", response_model=Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # In a real app, create JWT token
    # For demo, just use a simple string
    access_token = f"token_{user.email}"
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/users", response_model=UserResponse)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = get_user_by_email(db, user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return create_user(db, user.email, user.password)

@app.get("/users/me", response_model=UserResponse)
def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

@app.post("/documents", response_model=DocumentResponse)
def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Import ensure_dir_exists from config
    from config import ensure_dir_exists
    
    # Create directory for user if it doesn't exist
    user_dir = f"{STORAGE_PATH}/temp/{current_user.id}"
    ensure_dir_exists(user_dir)
    
    # Save file
    file_path = f"{user_dir}/{file.filename}"
    try:
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not save file: {str(e)}")
    
    # Get file size
    file_size = os.path.getsize(file_path)
    
    # Create document in database
    db_document = Document(
        filename=file.filename,
        file_path=file_path,
        file_size=file_size,
        mime_type=file.content_type,
        owner_id=current_user.id
    )
    db.add(db_document)
    db.commit()
    db.refresh(db_document)
    
    # Process document in background
    background_tasks.add_task(process_document_task, db, db_document.id)
    
    return db_document

@app.get("/documents", response_model=List[DocumentResponse])
def list_documents(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    documents = db.query(Document).filter(Document.owner_id == current_user.id).all()
    return documents

@app.get("/documents/{document_id}", response_model=DocumentResponse)
def get_document(document_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    document = get_document_by_id(db, document_id, current_user.id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document

@app.delete("/documents/{document_id}")
def delete_document(document_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    document = get_document_by_id(db, document_id, current_user.id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    success = delete_document_and_related_data(db, document_id)
    if not success:
        raise HTTPException(status_code=500, detail="Error deleting document")
    
    return {"message": "Document deleted successfully"}

@app.get("/documents/{document_id}/download")
def download_document(document_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    document = get_document_by_id(db, document_id, current_user.id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    if not os.path.exists(document.file_path):
        raise HTTPException(status_code=404, detail="Document file not found")
    
    return FileResponse(document.file_path, filename=document.filename, media_type=document.mime_type)

@app.get("/documents/{document_id}/analysis", response_model=AnalysisResultResponse)
def get_document_analysis(document_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    document = get_document_by_id(db, document_id, current_user.id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    analysis_result = get_analysis_result(db, document_id)
    if not analysis_result:
        raise HTTPException(status_code=404, detail="Analysis result not found")
    
    # Parse key figures JSON
    try:
        key_figures = json.loads(analysis_result.key_figures)
    except:
        key_figures = []
    
    # Create response
    response = {
        "id": analysis_result.id,
        "summary": analysis_result.summary,
        "key_figures": key_figures,
        "created_at": analysis_result.created_at
    }
    
    return response

@app.post("/documents/{document_id}/ask", response_model=QuestionResponse)
def ask_document_question(
    document_id: int,
    question_request: QuestionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    document = get_document_by_id(db, document_id, current_user.id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    analysis_result = get_analysis_result(db, document_id)
    if not analysis_result:
        raise HTTPException(status_code=404, detail="Analysis result not found")
    
    # Create or get QA session
    qa_session = db.query(QASession).filter(QASession.document_id == document_id).order_by(QASession.created_at.desc()).first()
    if not qa_session:
        qa_session = create_qa_session(db, document_id)
    
    # Ask question
    result = ask_question(analysis_result.vector_db_path, question_request.question)
    
    # Create question in database
    db_question = create_question(
        db,
        qa_session.id,
        question_request.question,
        result["answer"],
        result["sources"]
    )
    
    # Parse sources JSON
    try:
        sources = json.loads(db_question.sources)
    except:
        sources = []
    
    # Create response
    response = {
        "id": db_question.id,
        "question_text": db_question.question_text,
        "answer_text": db_question.answer_text,
        "sources": sources,
        "created_at": db_question.created_at
    }
    
    return response

@app.get("/documents/{document_id}/questions", response_model=List[QuestionResponse])
def list_document_questions(document_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    document = get_document_by_id(db, document_id, current_user.id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Get questions for document
    questions = db.query(Question).join(QASession).filter(QASession.document_id == document_id).all()
    
    # Create response
    response = []
    for question in questions:
        # Parse sources JSON
        try:
            sources = json.loads(question.sources)
        except:
            sources = []
        
        response.append({
            "id": question.id,
            "question_text": question.question_text,
            "answer_text": question.answer_text,
            "sources": sources,
            "created_at": question.created_at
        })
    
    return response

@app.get("/documents/{document_id}/export")
def export_document_analysis(document_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    document = get_document_by_id(db, document_id, current_user.id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    analysis_result = get_analysis_result(db, document_id)
    if not analysis_result:
        raise HTTPException(status_code=404, detail="Analysis result not found")
    
    # Create CSV in memory
    output = io.StringIO()
    
    # Write document info and summary
    output.write("Category,Value\n")
    output.write(f"Document,{document.filename}\n")
    output.write(f"Uploaded,{document.created_at}\n")
    output.write(f"Processed,{document.updated_at}\n")
    output.write("Summary,\n")
    
    # Fix the f-string issue by pre-processing the string
    summary_text = analysis_result.summary.replace(',', ' ').replace('\n', ' ')
    output.write(f"{summary_text}\n\n")
    
    # Add key figures
    if analysis_result.key_figures:
        output.write("Key Figures\n")
        try:
            key_figures = json.loads(analysis_result.key_figures)
            output.write("Name,Value,Source Page\n")
            for figure in key_figures:
                name = figure.get("name", "").replace(",", " ")
                value = figure.get("value", "").replace(",", " ")
                source_page = figure.get("source_page", "")
                output.write(f"{name},{value},{source_page}\n")
        except:
            output.write("Error parsing key figures\n")
    
    # Get questions for document
    questions = db.query(Question).join(QASession).filter(QASession.document_id == document_id).all()
    
    # Add questions and answers
    if questions:
        output.write("\nQuestions and Answers\n")
        for question in questions:
            output.write(f"\nQ: {question.question_text}\n")
            output.write(f"A: {question.answer_text}\n")
    
    # Return CSV
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment;filename=analysis_{document_id}.csv"}
    )

@app.get("/llm/status", response_model=LLMStatusResponse)
def get_llm_status_endpoint(current_user: User = Depends(get_current_user)):
    return get_llm_status()

@app.post("/llm/mode", response_model=LLMStatusResponse)
def set_llm_mode_endpoint(request: LLMModeRequest, current_user: User = Depends(get_current_user)):
    result = set_llm_mode(request.mode, request.api_key, request.model)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return get_llm_status()

@app.get("/llm/modes", response_model=List[str])
def get_available_llm_modes_endpoint(current_user: User = Depends(get_current_user)):
    return get_available_llm_modes()

@app.get("/health")
def health_check():
    """Health check endpoint with detailed status information."""
    status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "components": {
            "database": {
                "status": "unknown",
                "details": {}
            },
            "minio": {
                "status": "unknown",
                "details": {}
            },
            "llm": {
                "status": "unknown",
                "details": {}
            },
            "filesystem": {
                "status": "unknown",
                "details": {}
            }
        }
    }
    
    # Check database
    try:
        with SessionLocal() as db:
            db.execute("SELECT 1")
        status["components"]["database"]["status"] = "healthy"
    except Exception as e:
        status["components"]["database"]["status"] = "unhealthy"
        status["components"]["database"]["details"]["error"] = str(e)
        status["status"] = "degraded"
    
    # Check MinIO
    if minio_client:
        try:
            minio_client.bucket_exists(DOCUMENTS_BUCKET)
            status["components"]["minio"]["status"] = "healthy"
        except Exception as e:
            status["components"]["minio"]["status"] = "unhealthy"
            status["components"]["minio"]["details"]["error"] = str(e)
            status["status"] = "degraded"
    else:
        status["components"]["minio"]["status"] = "not_configured"
    
    # Check LLM
    try:
        llm_status = get_llm_status()
        status["components"]["llm"]["status"] = llm_status["status"]
        status["components"]["llm"]["details"] = {
            "mode": llm_status["mode"],
            "model": llm_status["model"]
        }
        if llm_status["status"] != "available":
            status["status"] = "degraded"
    except Exception as e:
        status["components"]["llm"]["status"] = "unhealthy"
        status["components"]["llm"]["details"]["error"] = str(e)
        status["status"] = "degraded"
    
    # Check filesystem
    try:
        # Check if directories exist and are writable
        dirs_to_check = [
            STORAGE_PATH,
            f"{STORAGE_PATH}/temp",
            f"{STORAGE_PATH}/db",
            f"{STORAGE_PATH}/vector_db",
            f"{STORAGE_PATH}/cache"
        ]
        
        dir_status = {}
        for dir_path in dirs_to_check:
            if not os.path.exists(dir_path):
                dir_status[dir_path] = "missing"
                status["status"] = "degraded"
            elif not os.access(dir_path, os.W_OK):
                dir_status[dir_path] = "not_writable"
                status["status"] = "degraded"
            else:
                dir_status[dir_path] = "ok"
        
        status["components"]["filesystem"]["status"] = "healthy" if all(s == "ok" for s in dir_status.values()) else "degraded"
        status["components"]["filesystem"]["details"]["directories"] = dir_status
    except Exception as e:
        status["components"]["filesystem"]["status"] = "unhealthy"
        status["components"]["filesystem"]["details"]["error"] = str(e)
        status["status"] = "degraded"
    
    return status

# Startup event
@app.on_event("startup")
def startup_event():
    logger.info("Starting FastAPI application")
    
    # Create demo user if not exists
    with SessionLocal() as db:
        demo_user = get_user_by_email(db, "demo@example.com")
        if not demo_user:
            logger.info("Creating demo user on startup")
            create_user(db, "demo@example.com", "demo123")
            logger.info("Demo user created successfully")

# Run the application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

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
from typing import List, Dict, Any, Optional

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
    QuestionRequest, QuestionResponse, LLMStatusResponse, LLMModeRequest,
    AdminUserCreate, AdminUserUpdate, AdminUserResponse, AdminUserListResponse,
    LLMVendorConfig, LLMConfigResponse, LLMModelListResponse,
    StorageOverviewResponse, UserStorageResponse, StorageCleanupResult
)
from config import engine, SessionLocal, STORAGE_PATH, DOCUMENTS_BUCKET, minio_client
from auth import get_db, get_current_user, get_current_admin_user
from utils import (
    authenticate_user, create_user, get_user_by_email, get_document_by_id,
    get_analysis_result, create_qa_session, create_question,
    delete_document_and_related_data, get_all_users, get_user_count,
    get_user_by_id, create_admin_user, update_user, delete_user,
    get_user_document_count
)
from llm_config import (
    SUPPORTED_VENDORS, load_llm_config, save_llm_config, get_vendor_models,
    validate_config, test_llm_connection
)
from storage_management import (
    get_storage_overview, get_user_storage_details, cleanup_user_storage,
    cleanup_orphaned_files
)
from background_tasks import process_document_task, task_manager
from llm_integration import (
    ask_question, get_llm_status, set_llm_mode, get_available_llm_modes,
    clear_document_cache, clear_all_cache
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
    return create_user(db, user.email, user.password, user.full_name)

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

    # Cancel any running processing task for this document
    if task_manager.is_task_running(document_id):
        task_manager.cancel_task(document_id)
        logger.info(f"Cancelled processing task for document {document_id} before deletion")

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
    result = set_llm_mode(request.mode, request.api_key, request.model, request.base_url)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return get_llm_status()

@app.get("/llm/modes", response_model=List[str])
def get_available_llm_modes_endpoint(current_user: User = Depends(get_current_user)):
    return get_available_llm_modes()

@app.post("/documents/{document_id}/cancel")
def cancel_document_processing(document_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Cancel processing of a document."""
    document = get_document_by_id(db, document_id, current_user.id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    if task_manager.is_task_running(document_id):
        success = task_manager.cancel_task(document_id)
        if success:
            # Update document status to CANCELLED
            document.status = "CANCELLED"
            db.commit()
            return {"message": f"Processing cancelled for document {document_id}"}
        else:
            raise HTTPException(status_code=500, detail="Failed to cancel processing")
    else:
        return {"message": f"No active processing found for document {document_id}"}

@app.get("/documents/{document_id}/status")
def get_document_processing_status(document_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get processing status of a document."""
    document = get_document_by_id(db, document_id, current_user.id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    is_processing = task_manager.is_task_running(document_id)
    return {
        "document_id": document_id,
        "status": document.status,
        "is_processing": is_processing,
        "can_cancel": is_processing and document.status == "PROCESSING"
    }

@app.post("/documents/{document_id}/clear-cache")
def clear_document_cache_endpoint(document_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Clear cache for a specific document to force reprocessing."""
    document = get_document_by_id(db, document_id, current_user.id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    success = clear_document_cache(str(document_id))
    if success:
        return {"message": f"Cache cleared for document {document_id}"}
    else:
        raise HTTPException(status_code=500, detail="Failed to clear cache")

# Admin endpoints
@app.get("/admin/users", response_model=AdminUserListResponse)
def get_users_admin(
    page: int = 1,
    per_page: int = 20,
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get all users (admin only)."""
    skip = (page - 1) * per_page
    users = get_all_users(db, skip=skip, limit=per_page)
    total = get_user_count(db)
    total_pages = (total + per_page - 1) // per_page

    # Add document count for each user
    admin_users = []
    for user in users:
        doc_count = get_user_document_count(db, user.id)
        admin_user_data = AdminUserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            is_active=user.is_active,
            is_admin=user.is_admin,
            last_login=user.last_login,
            created_at=user.created_at,
            updated_at=user.updated_at,
            document_count=doc_count
        )
        admin_users.append(admin_user_data)

    return AdminUserListResponse(
        users=admin_users,
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages
    )

@app.post("/admin/users", response_model=AdminUserResponse)
def create_user_admin(
    user_data: AdminUserCreate,
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Create a new user (admin only)."""
    # Check if email already exists
    existing_user = get_user_by_email(db, user_data.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = create_admin_user(
        db=db,
        email=user_data.email,
        password=user_data.password,
        full_name=user_data.full_name,
        is_active=user_data.is_active,
        is_admin=user_data.is_admin
    )

    doc_count = get_user_document_count(db, new_user.id)
    return AdminUserResponse(
        id=new_user.id,
        email=new_user.email,
        full_name=new_user.full_name,
        is_active=new_user.is_active,
        is_admin=new_user.is_admin,
        last_login=new_user.last_login,
        created_at=new_user.created_at,
        updated_at=new_user.updated_at,
        document_count=doc_count
    )

@app.get("/admin/users/{user_id}", response_model=AdminUserResponse)
def get_user_admin(
    user_id: int,
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get a specific user (admin only)."""
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    doc_count = get_user_document_count(db, user.id)
    return AdminUserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        is_admin=user.is_admin,
        last_login=user.last_login,
        created_at=user.created_at,
        updated_at=user.updated_at,
        document_count=doc_count
    )

@app.put("/admin/users/{user_id}", response_model=AdminUserResponse)
def update_user_admin(
    user_id: int,
    user_data: AdminUserUpdate,
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Update a user (admin only)."""
    # Check if user exists
    existing_user = get_user_by_id(db, user_id)
    if not existing_user:
        raise HTTPException(status_code=404, detail="User not found")

    # Check if email is being changed and if it already exists
    if user_data.email and user_data.email != existing_user.email:
        email_user = get_user_by_email(db, user_data.email)
        if email_user:
            raise HTTPException(status_code=400, detail="Email already registered")

    updated_user = update_user(
        db=db,
        user_id=user_id,
        email=user_data.email,
        full_name=user_data.full_name,
        is_active=user_data.is_active,
        is_admin=user_data.is_admin,
        password=user_data.password
    )

    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found")

    doc_count = get_user_document_count(db, updated_user.id)
    return AdminUserResponse(
        id=updated_user.id,
        email=updated_user.email,
        full_name=updated_user.full_name,
        is_active=updated_user.is_active,
        is_admin=updated_user.is_admin,
        last_login=updated_user.last_login,
        created_at=updated_user.created_at,
        updated_at=updated_user.updated_at,
        document_count=doc_count
    )

@app.delete("/admin/users/{user_id}")
def delete_user_admin(
    user_id: int,
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Delete a user (admin only)."""
    # Prevent admin from deleting themselves
    if user_id == admin_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")

    success = delete_user(db, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")

    return {"message": "User deleted successfully"}

# LLM Configuration endpoints (Admin only)
@app.get("/admin/llm/config", response_model=LLMConfigResponse)
def get_llm_config_admin(admin_user: User = Depends(get_current_admin_user)):
    """Get current LLM configuration (admin only)."""
    try:
        current_config = load_llm_config()

        # Get available models for each vendor
        vendor_models = {}
        for vendor_key, vendor_info in SUPPORTED_VENDORS.items():
            try:
                models = get_vendor_models(vendor_key)
                vendor_models[vendor_key] = models
            except Exception as e:
                logger.warning(f"Could not fetch models for {vendor_key}: {e}")
                vendor_models[vendor_key] = vendor_info["default_models"]

        return LLMConfigResponse(
            current_vendor=current_config.get("vendor", "openai"),
            current_model=current_config.get("model"),
            current_config=current_config,
            available_vendors=list(SUPPORTED_VENDORS.keys()),
            vendor_models=vendor_models,
            status="success"
        )
    except Exception as e:
        logger.error(f"Error getting LLM config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/admin/llm/config")
def update_llm_config_admin(
    config: LLMVendorConfig,
    admin_user: User = Depends(get_current_admin_user)
):
    """Update LLM configuration (admin only)."""
    try:
        logger.info(f"Received LLM config update: {config}")

        # Convert to dict
        config_dict = {
            "vendor": config.vendor,
            "api_key": config.api_key,
            "base_url": config.base_url,
            "model": config.model,
            "temperature": config.temperature or 0.3,
            "max_tokens": config.max_tokens or 2000,
            "timeout": config.timeout or 300
        }

        logger.info(f"Config dict: {config_dict}")

        # Validate configuration
        validation = validate_config(config_dict)
        logger.info(f"Validation result: {validation}")

        if not validation["valid"]:
            logger.error(f"Validation failed: {validation['errors']}")
            raise HTTPException(status_code=400, detail={"errors": validation["errors"]})

        # Save configuration
        if not save_llm_config(config_dict):
            raise HTTPException(status_code=500, detail="Failed to save configuration")

        return {"message": "LLM configuration updated successfully", "config": config_dict}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating LLM config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/admin/llm/vendors")
def get_llm_vendors_admin(admin_user: User = Depends(get_current_admin_user)):
    """Get available LLM vendors (admin only)."""
    return {
        "vendors": SUPPORTED_VENDORS
    }

@app.get("/admin/llm/models/{vendor}", response_model=LLMModelListResponse)
def get_vendor_models_admin(
    vendor: str,
    base_url: Optional[str] = None,
    api_key: Optional[str] = None,
    admin_user: User = Depends(get_current_admin_user)
):
    """Get available models for a specific vendor (admin only)."""
    try:
        if vendor not in SUPPORTED_VENDORS:
            raise HTTPException(status_code=400, detail=f"Unsupported vendor: {vendor}")

        models = get_vendor_models(vendor, base_url, api_key)
        return LLMModelListResponse(
            vendor=vendor,
            models=models
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting models for {vendor}: {e}")
        return LLMModelListResponse(
            vendor=vendor,
            models=SUPPORTED_VENDORS[vendor]["default_models"],
            error=str(e)
        )

@app.post("/admin/llm/test")
def test_llm_config_admin(
    config: LLMVendorConfig,
    admin_user: User = Depends(get_current_admin_user)
):
    """Test LLM configuration (admin only)."""
    try:
        config_dict = {
            "vendor": config.vendor,
            "api_key": config.api_key,
            "base_url": config.base_url,
            "model": config.model,
            "temperature": config.temperature or 0.3,
            "max_tokens": config.max_tokens or 2000,
            "timeout": config.timeout or 300
        }

        result = test_llm_connection(config_dict)
        return result
    except Exception as e:
        logger.error(f"Error testing LLM config: {e}")
        return {"success": False, "error": str(e)}

# Storage Management endpoints (Admin only)
@app.get("/admin/storage/overview", response_model=StorageOverviewResponse)
def get_storage_overview_admin(admin_user: User = Depends(get_current_admin_user)):
    """Get storage overview (admin only)."""
    try:
        overview = get_storage_overview()
        return StorageOverviewResponse(**overview)
    except Exception as e:
        logger.error(f"Error getting storage overview: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/admin/storage/users", response_model=UserStorageResponse)
def get_user_storage_admin(
    user_id: Optional[int] = None,
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get user storage details (admin only)."""
    try:
        user_storage = get_user_storage_details(db, user_id)
        return UserStorageResponse(users=user_storage)
    except Exception as e:
        logger.error(f"Error getting user storage details: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/admin/storage/cleanup/user/{user_id}", response_model=StorageCleanupResult)
def cleanup_user_storage_admin(
    user_id: int,
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Clean up storage for a specific user (admin only)."""
    try:
        # Check if user exists
        user = get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        result = cleanup_user_storage(db, user_id)
        return StorageCleanupResult(**result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cleaning up user storage: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/admin/storage/cleanup/orphaned", response_model=StorageCleanupResult)
def cleanup_orphaned_files_admin(admin_user: User = Depends(get_current_admin_user)):
    """Clean up orphaned files (admin only)."""
    try:
        result = cleanup_orphaned_files()
        return StorageCleanupResult(**result)
    except Exception as e:
        logger.error(f"Error cleaning up orphaned files: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/admin/clear-all-cache")
def clear_all_cache_endpoint(current_user: User = Depends(get_current_user)):
    """Clear all cache data (admin function)."""
    success = clear_all_cache()
    if success:
        return {"message": "All cache cleared successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to clear all cache")

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
            create_user(db, "demo@example.com", "demo123", "Demo User")
            logger.info("Demo user created successfully")

        # Create admin user if not exists
        admin_user = get_user_by_email(db, "admin@example.com")
        if not admin_user:
            logger.info("Creating admin user on startup")
            create_admin_user(db, "admin@example.com", "admin123", "Admin User", is_active=True, is_admin=True)
            logger.info("Admin user created successfully")

# Run the application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

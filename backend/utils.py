import os
import json
import shutil
import logging
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from models import User, Document, AnalysisResult, QASession, Question
from config import STORAGE_PATH, DOCUMENTS_BUCKET, minio_client

logger = logging.getLogger(__name__)

# Authentication utilities
def get_password_hash(password: str) -> str:
    """Hash password. In a real app, use proper password hashing like bcrypt."""
    return f"hashed_{password}"

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password. In a real app, use proper password verification."""
    return hashed_password == f"hashed_{plain_password}"

# Database utilities
def get_user_by_email(db: Session, email: str):
    """Get user by email."""
    return db.query(User).filter(User.email == email).first()

def authenticate_user(db: Session, email: str, password: str):
    """Authenticate user with email and password."""
    user = get_user_by_email(db, email)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

def create_user(db: Session, email: str, password: str):
    """Create a new user."""
    hashed_password = get_password_hash(password)
    db_user = User(email=email, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_document_by_id(db: Session, document_id: int, user_id: int):
    """Get document by ID for a specific user."""
    return db.query(Document).filter(Document.id == document_id, Document.owner_id == user_id).first()

def get_analysis_result(db: Session, document_id: int):
    """Get analysis result for a document."""
    return db.query(AnalysisResult).filter(AnalysisResult.document_id == document_id).first()

def create_qa_session(db: Session, document_id: int):
    """Create a new QA session for a document."""
    db_session = QASession(document_id=document_id)
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session

def create_question(db: Session, session_id: int, question: str, answer: str, sources: List[Dict[str, Any]]):
    """Create a new question in a QA session."""
    db_question = Question(
        question_text=question,
        answer_text=answer,
        sources=json.dumps(sources),
        session_id=session_id
    )
    db.add(db_question)
    db.commit()
    db.refresh(db_question)
    return db_question

def delete_document_and_related_data(db: Session, document_id: int):
    """Delete a document and all related data."""
    try:
        # Get document
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            logger.error(f"Document not found for deletion: {document_id}")
            return False
        
        # Get analysis result for vector DB path
        analysis_result = db.query(AnalysisResult).filter(AnalysisResult.document_id == document_id).first()
        
        # Delete file from storage
        if document.file_path and os.path.exists(document.file_path):
            try:
                os.remove(document.file_path)
                logger.info(f"Deleted document file: {document.file_path}")
            except Exception as e:
                logger.error(f"Error deleting document file: {e}")
        
        # Delete from MinIO if available
        if minio_client:
            try:
                # List all objects with document_id prefix and delete them
                objects = minio_client.list_objects(DOCUMENTS_BUCKET, prefix=str(document_id))
                for obj in objects:
                    minio_client.remove_object(DOCUMENTS_BUCKET, obj.object_name)
                logger.info(f"Deleted objects from MinIO for document: {document_id}")
            except Exception as e:
                logger.error(f"Error deleting from MinIO: {e}")
        
        # Delete vector DB if exists
        if analysis_result and analysis_result.vector_db_path and os.path.exists(analysis_result.vector_db_path):
            try:
                shutil.rmtree(analysis_result.vector_db_path)
                logger.info(f"Deleted vector DB: {analysis_result.vector_db_path}")
            except Exception as e:
                logger.error(f"Error deleting vector DB: {e}")
        
        # Delete cache files
        cache_dir = f"{STORAGE_PATH}/cache"
        if os.path.exists(cache_dir):
            try:
                cache_files = [f for f in os.listdir(cache_dir) if f.startswith(f"{document_id}_")]
                for file in cache_files:
                    os.remove(os.path.join(cache_dir, file))
                logger.info(f"Deleted {len(cache_files)} cache files for document: {document_id}")
            except Exception as e:
                logger.error(f"Error deleting cache files: {e}")
        
        # Delete document from database (will cascade delete analysis results and QA sessions)
        db.delete(document)
        db.commit()
        
        logger.info(f"Document and related data deleted successfully: {document_id}")
        return True
    except Exception as e:
        logger.error(f"Error in delete_document_and_related_data: {str(e)}")
        return False
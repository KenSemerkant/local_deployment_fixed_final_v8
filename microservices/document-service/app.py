"""
Document Service - Handles document upload, storage, and metadata management.
Implements clean architecture with domain, application, and infrastructure layers.
"""

import os
import logging
from datetime import datetime
from typing import List
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, BackgroundTasks, Request
from sqlalchemy.orm import Session

# Domain layer imports
from domain.entities import Document, DocumentStatus
from domain.repositories import IDocumentRepository, IStorageRepository

# Application layer imports
from application.use_cases import UploadDocumentUseCase, GetUserDocumentsUseCase, DeleteDocumentUseCase
from application.schemas import DocumentResponse, DocumentListResponse

# Infrastructure layer imports
from infrastructure.database import get_db
from infrastructure.repositories import SQLAlchemyDocumentRepository, MinIOStorageRepository
from infrastructure.auth import get_current_user_from_headers
from infrastructure.external_services import UserServiceClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(title="Document Service", version="1.0.0")

# External service clients
user_service = UserServiceClient(os.getenv("USER_SERVICE_URL", "http://user-service:8001"))


# Dependency injection
def get_document_repository(db: Session = Depends(get_db)) -> IDocumentRepository:
    return SQLAlchemyDocumentRepository(db)


def get_storage_repository() -> IStorageRepository:
    return MinIOStorageRepository(
        endpoint=os.getenv("MINIO_ENDPOINT", "minio:9000"),
        access_key=os.getenv("MINIO_ACCESS_KEY", "minioadmin"),
        secret_key=os.getenv("MINIO_SECRET_KEY", "minioadmin")
    )


def get_upload_document_use_case(
    document_repo: IDocumentRepository = Depends(get_document_repository),
    storage_repo: IStorageRepository = Depends(get_storage_repository)
) -> UploadDocumentUseCase:
    return UploadDocumentUseCase(document_repo, storage_repo)


def get_user_documents_use_case(
    document_repo: IDocumentRepository = Depends(get_document_repository)
) -> GetUserDocumentsUseCase:
    return GetUserDocumentsUseCase(document_repo)


def get_delete_document_use_case(
    document_repo: IDocumentRepository = Depends(get_document_repository),
    storage_repo: IStorageRepository = Depends(get_storage_repository)
) -> DeleteDocumentUseCase:
    return DeleteDocumentUseCase(document_repo, storage_repo)


# Document endpoints
@app.post("/documents", response_model=DocumentResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    request: Request = None,
    upload_use_case: UploadDocumentUseCase = Depends(get_upload_document_use_case)
):
    """Upload a new document."""
    # Get user info from headers (set by API Gateway)
    user_info = get_current_user_from_headers(request)
    
    try:
        # Read file content
        content = await file.read()
        
        # Upload document
        document = upload_use_case.execute(
            user_id=user_info["id"],
            filename=file.filename,
            content=content,
            content_type=file.content_type or "application/octet-stream"
        )
        
        # Trigger document processing in background
        background_tasks.add_task(trigger_document_processing, document.id)
        
        return DocumentResponse.from_entity(document)
        
    except Exception as e:
        logger.error(f"Error uploading document: {e}")
        raise HTTPException(status_code=500, detail="Failed to upload document")


@app.get("/documents", response_model=DocumentListResponse)
async def get_user_documents(
    skip: int = 0,
    limit: int = 100,
    request: Request = None,
    get_documents_use_case: GetUserDocumentsUseCase = Depends(get_user_documents_use_case)
):
    """Get user's documents."""
    user_info = get_current_user_from_headers(request)
    
    documents = get_documents_use_case.execute(user_info["id"], skip, limit)
    return DocumentListResponse(
        documents=[DocumentResponse.from_entity(doc) for doc in documents],
        total=len(documents),
        skip=skip,
        limit=limit
    )


@app.get("/documents/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: int,
    request: Request = None,
    document_repo: IDocumentRepository = Depends(get_document_repository)
):
    """Get document by ID."""
    user_info = get_current_user_from_headers(request)
    
    document = document_repo.get_by_id(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Check ownership or admin privileges
    if document.owner_id != user_info["id"] and not user_info.get("is_admin", False):
        raise HTTPException(status_code=403, detail="Access denied")
    
    return DocumentResponse.from_entity(document)


@app.delete("/documents/{document_id}")
async def delete_document(
    document_id: int,
    request: Request = None,
    delete_use_case: DeleteDocumentUseCase = Depends(get_delete_document_use_case)
):
    """Delete document."""
    user_info = get_current_user_from_headers(request)
    
    success = delete_use_case.execute(document_id, user_info["id"], user_info.get("is_admin", False))
    if not success:
        raise HTTPException(status_code=404, detail="Document not found or access denied")
    
    return {"message": "Document deleted successfully"}


@app.get("/documents/{document_id}/download")
async def download_document(
    document_id: int,
    request: Request = None,
    document_repo: IDocumentRepository = Depends(get_document_repository),
    storage_repo: IStorageRepository = Depends(get_storage_repository)
):
    """Download document content."""
    user_info = get_current_user_from_headers(request)
    
    document = document_repo.get_by_id(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Check ownership or admin privileges
    if document.owner_id != user_info["id"] and not user_info.get("is_admin", False):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get file content from storage
    content = storage_repo.download_file(document.file_path)
    if not content:
        raise HTTPException(status_code=404, detail="File not found in storage")
    
    from fastapi.responses import Response
    return Response(
        content=content,
        media_type=document.mime_type,
        headers={"Content-Disposition": f"attachment; filename={document.filename}"}
    )


@app.put("/documents/{document_id}/status")
async def update_document_status(
    document_id: int,
    status: str,
    request: Request = None,
    document_repo: IDocumentRepository = Depends(get_document_repository)
):
    """Update document status (internal use)."""
    # This endpoint is for internal service communication
    document = document_repo.get_by_id(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    try:
        document.status = DocumentStatus(status)
        document.updated_at = datetime.utcnow()
        updated_document = document_repo.update(document)
        return DocumentResponse.from_entity(updated_document)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid status")


# Admin endpoints
@app.get("/admin/documents", response_model=DocumentListResponse)
async def get_all_documents(
    skip: int = 0,
    limit: int = 100,
    request: Request = None,
    document_repo: IDocumentRepository = Depends(get_document_repository)
):
    """Get all documents (admin only)."""
    user_info = get_current_user_from_headers(request)
    if not user_info.get("is_admin", False):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    documents = document_repo.get_all(skip, limit)
    return DocumentListResponse(
        documents=[DocumentResponse.from_entity(doc) for doc in documents],
        total=len(documents),
        skip=skip,
        limit=limit
    )


# Background tasks
async def trigger_document_processing(document_id: int):
    """Trigger document processing in the analysis service."""
    try:
        import httpx
        analysis_service_url = os.getenv("ANALYSIS_SERVICE_URL", "http://analysis-service:8003")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{analysis_service_url}/internal/process-document/{document_id}",
                timeout=5.0
            )
            if response.status_code == 200:
                logger.info(f"Document {document_id} processing triggered successfully")
            else:
                logger.error(f"Failed to trigger processing for document {document_id}")
                
    except Exception as e:
        logger.error(f"Error triggering document processing: {e}")


# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "document-service",
        "timestamp": datetime.utcnow().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)

"""
Storage Management Module for Admin Functions
Provides comprehensive storage analysis and management capabilities.
"""

import os
import json
import logging
import shutil
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
from sqlalchemy.orm import Session
from sqlalchemy import func

from models import User, Document, AnalysisResult, QASession, Question
from config import STORAGE_PATH, DOCUMENTS_BUCKET, minio_client

logger = logging.getLogger(__name__)

def get_directory_size(path: str) -> int:
    """Calculate total size of directory in bytes."""
    total_size = 0
    try:
        for dirpath, dirnames, filenames in os.walk(path):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                if os.path.exists(filepath):
                    total_size += os.path.getsize(filepath)
    except Exception as e:
        logger.error(f"Error calculating directory size for {path}: {e}")
    return total_size

def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format."""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"

def get_file_count(path: str) -> int:
    """Count total number of files in directory."""
    count = 0
    try:
        for dirpath, dirnames, filenames in os.walk(path):
            count += len(filenames)
    except Exception as e:
        logger.error(f"Error counting files in {path}: {e}")
    return count

def get_storage_overview() -> Dict[str, Any]:
    """Get comprehensive storage overview."""
    try:
        storage_info = {
            "total_size": 0,
            "total_files": 0,
            "directories": {},
            "last_updated": datetime.utcnow().isoformat()
        }
        
        # Define storage directories
        directories = {
            "database": f"{STORAGE_PATH}/db",
            "documents": f"{STORAGE_PATH}/temp",  # Local temp storage
            "vector_db": f"{STORAGE_PATH}/vector_db",
            "cache": f"{STORAGE_PATH}/cache"
        }
        
        for name, path in directories.items():
            if os.path.exists(path):
                size = get_directory_size(path)
                file_count = get_file_count(path)
                
                storage_info["directories"][name] = {
                    "path": path,
                    "size_bytes": size,
                    "size_formatted": format_file_size(size),
                    "file_count": file_count,
                    "exists": True
                }
                
                storage_info["total_size"] += size
                storage_info["total_files"] += file_count
            else:
                storage_info["directories"][name] = {
                    "path": path,
                    "size_bytes": 0,
                    "size_formatted": "0 B",
                    "file_count": 0,
                    "exists": False
                }
        
        storage_info["total_size_formatted"] = format_file_size(storage_info["total_size"])
        
        # Add MinIO storage info if available
        if minio_client:
            try:
                minio_objects = list(minio_client.list_objects(DOCUMENTS_BUCKET, recursive=True))
                minio_size = sum(obj.size for obj in minio_objects if obj.size)
                minio_count = len(minio_objects)
                
                storage_info["directories"]["minio"] = {
                    "path": f"MinIO bucket: {DOCUMENTS_BUCKET}",
                    "size_bytes": minio_size,
                    "size_formatted": format_file_size(minio_size),
                    "file_count": minio_count,
                    "exists": True
                }
                
                storage_info["total_size"] += minio_size
                storage_info["total_files"] += minio_count
                storage_info["total_size_formatted"] = format_file_size(storage_info["total_size"])
                
            except Exception as e:
                logger.error(f"Error getting MinIO storage info: {e}")
                storage_info["directories"]["minio"] = {
                    "path": f"MinIO bucket: {DOCUMENTS_BUCKET}",
                    "size_bytes": 0,
                    "size_formatted": "Error",
                    "file_count": 0,
                    "exists": False,
                    "error": str(e)
                }
        
        return storage_info
        
    except Exception as e:
        logger.error(f"Error getting storage overview: {e}")
        return {
            "error": str(e),
            "total_size": 0,
            "total_files": 0,
            "directories": {},
            "last_updated": datetime.utcnow().isoformat()
        }

def get_user_storage_details(db: Session, user_id: Optional[int] = None) -> List[Dict[str, Any]]:
    """Get detailed storage information for users."""
    try:
        # Build query
        query = db.query(User)
        if user_id:
            query = query.filter(User.id == user_id)
        
        users = query.all()
        user_storage_data = []
        
        for user in users:
            user_data = {
                "user_id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "is_active": user.is_active,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "storage": {
                    "documents": {
                        "count": 0,
                        "total_size": 0,
                        "total_size_formatted": "0 B"
                    },
                    "cache": {
                        "count": 0,
                        "total_size": 0,
                        "total_size_formatted": "0 B"
                    },
                    "vector_db": {
                        "count": 0,
                        "total_size": 0,
                        "total_size_formatted": "0 B"
                    },
                    "analysis_results": 0,
                    "qa_sessions": 0,
                    "questions": 0
                }
            }
            
            # Get document statistics
            documents = db.query(Document).filter(Document.owner_id == user.id).all()
            user_data["storage"]["documents"]["count"] = len(documents)
            
            # Calculate document sizes
            total_doc_size = 0
            for doc in documents:
                if doc.file_path and os.path.exists(doc.file_path):
                    total_doc_size += os.path.getsize(doc.file_path)
                
                # Add MinIO document size if available
                if minio_client and doc.filename:
                    try:
                        obj_info = minio_client.stat_object(DOCUMENTS_BUCKET, f"{user.id}/{doc.filename}")
                        total_doc_size += obj_info.size
                    except Exception:
                        pass  # Object might not exist in MinIO
            
            user_data["storage"]["documents"]["total_size"] = total_doc_size
            user_data["storage"]["documents"]["total_size_formatted"] = format_file_size(total_doc_size)
            
            # Get cache statistics
            cache_dir = f"{STORAGE_PATH}/cache"
            if os.path.exists(cache_dir):
                cache_files = [f for f in os.listdir(cache_dir) if f.startswith(f"{user.id}_")]
                user_data["storage"]["cache"]["count"] = len(cache_files)
                
                cache_size = 0
                for cache_file in cache_files:
                    cache_path = os.path.join(cache_dir, cache_file)
                    if os.path.exists(cache_path):
                        cache_size += os.path.getsize(cache_path)
                
                user_data["storage"]["cache"]["total_size"] = cache_size
                user_data["storage"]["cache"]["total_size_formatted"] = format_file_size(cache_size)
            
            # Get vector DB statistics
            vector_db_dir = f"{STORAGE_PATH}/vector_db"
            if os.path.exists(vector_db_dir):
                user_vector_dirs = [d for d in os.listdir(vector_db_dir) 
                                  if os.path.isdir(os.path.join(vector_db_dir, d)) and d.startswith(str(user.id))]
                user_data["storage"]["vector_db"]["count"] = len(user_vector_dirs)
                
                vector_size = 0
                for vector_dir in user_vector_dirs:
                    vector_path = os.path.join(vector_db_dir, vector_dir)
                    vector_size += get_directory_size(vector_path)
                
                user_data["storage"]["vector_db"]["total_size"] = vector_size
                user_data["storage"]["vector_db"]["total_size_formatted"] = format_file_size(vector_size)
            
            # Get database statistics
            user_data["storage"]["analysis_results"] = db.query(AnalysisResult).join(Document).filter(Document.owner_id == user.id).count()
            user_data["storage"]["qa_sessions"] = db.query(QASession).join(Document).filter(Document.owner_id == user.id).count()
            user_data["storage"]["questions"] = db.query(Question).join(QASession).join(Document).filter(Document.owner_id == user.id).count()
            
            user_storage_data.append(user_data)
        
        return user_storage_data
        
    except Exception as e:
        logger.error(f"Error getting user storage details: {e}")
        return []

def cleanup_user_storage(db: Session, user_id: int) -> Dict[str, Any]:
    """Clean up all storage for a specific user."""
    try:
        result = {
            "success": True,
            "cleaned": {
                "documents": 0,
                "cache_files": 0,
                "vector_dbs": 0,
                "minio_objects": 0
            },
            "errors": []
        }
        
        # Get user documents
        documents = db.query(Document).filter(Document.owner_id == user_id).all()
        
        for doc in documents:
            try:
                # Delete local file
                if doc.file_path and os.path.exists(doc.file_path):
                    os.remove(doc.file_path)
                    result["cleaned"]["documents"] += 1
                
                # Delete MinIO object
                if minio_client and doc.filename:
                    try:
                        minio_client.remove_object(DOCUMENTS_BUCKET, f"{user_id}/{doc.filename}")
                        result["cleaned"]["minio_objects"] += 1
                    except Exception as e:
                        result["errors"].append(f"MinIO cleanup error for {doc.filename}: {str(e)}")
                
            except Exception as e:
                result["errors"].append(f"Document cleanup error for {doc.id}: {str(e)}")
        
        # Clean cache files
        cache_dir = f"{STORAGE_PATH}/cache"
        if os.path.exists(cache_dir):
            cache_files = [f for f in os.listdir(cache_dir) if f.startswith(f"{user_id}_")]
            for cache_file in cache_files:
                try:
                    os.remove(os.path.join(cache_dir, cache_file))
                    result["cleaned"]["cache_files"] += 1
                except Exception as e:
                    result["errors"].append(f"Cache cleanup error for {cache_file}: {str(e)}")
        
        # Clean vector DB directories
        vector_db_dir = f"{STORAGE_PATH}/vector_db"
        if os.path.exists(vector_db_dir):
            user_vector_dirs = [d for d in os.listdir(vector_db_dir) 
                              if os.path.isdir(os.path.join(vector_db_dir, d)) and d.startswith(str(user_id))]
            for vector_dir in user_vector_dirs:
                try:
                    shutil.rmtree(os.path.join(vector_db_dir, vector_dir))
                    result["cleaned"]["vector_dbs"] += 1
                except Exception as e:
                    result["errors"].append(f"Vector DB cleanup error for {vector_dir}: {str(e)}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error cleaning up user storage: {e}")
        return {
            "success": False,
            "error": str(e),
            "cleaned": {"documents": 0, "cache_files": 0, "vector_dbs": 0, "minio_objects": 0},
            "errors": [str(e)]
        }

def cleanup_orphaned_files() -> Dict[str, Any]:
    """Clean up orphaned files that don't belong to any user or document."""
    try:
        result = {
            "success": True,
            "cleaned": {
                "cache_files": 0,
                "vector_dbs": 0,
                "temp_files": 0
            },
            "errors": []
        }
        
        # This would require database access to check which files are orphaned
        # For now, we'll implement a basic cleanup of old temp files
        
        temp_dir = f"{STORAGE_PATH}/temp"
        if os.path.exists(temp_dir):
            # Clean files older than 24 hours
            cutoff_time = datetime.now().timestamp() - (24 * 60 * 60)
            
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        if os.path.getmtime(file_path) < cutoff_time:
                            os.remove(file_path)
                            result["cleaned"]["temp_files"] += 1
                    except Exception as e:
                        result["errors"].append(f"Temp file cleanup error for {file}: {str(e)}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error cleaning up orphaned files: {e}")
        return {
            "success": False,
            "error": str(e),
            "cleaned": {"cache_files": 0, "vector_dbs": 0, "temp_files": 0},
            "errors": [str(e)]
        }

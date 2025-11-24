from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import shutil
from pathlib import Path
import uuid
import math

# Pydantic models
class StorageDirectoryInfo(BaseModel):
    path: str
    size_bytes: int
    size_formatted: str
    file_count: int
    exists: bool
    error: Optional[str] = None

class StorageOverviewResponse(BaseModel):
    total_size: int
    total_size_formatted: str
    total_files: int
    directories: Dict[str, StorageDirectoryInfo]
    last_updated: str
    error: Optional[str] = None

class UserStorageInfo(BaseModel):
    user_id: int
    email: str
    full_name: Optional[str]
    is_active: bool
    storage: Dict[str, Any]

class UserStorageResponse(BaseModel):
    users: List[UserStorageInfo]

class CleanupItem(BaseModel):
    name: str
    count: int

class CleanupResult(BaseModel):
    success: bool
    cleaned_items: List[CleanupItem]
    errors: List[str]
    message: str

class StorageCleanupRequest(BaseModel):
    bucket: str
    retention_days: int

# Initialize FastAPI app
app = FastAPI(
    title="Storage Management Service",
    version="1.0.0",
    root_path="/storage"
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
DIRECTORIES = {
    "documents": os.path.join(STORAGE_PATH, "documents"),
    "temp": os.path.join(STORAGE_PATH, "temp"),
    "vector_dbs": os.path.join(STORAGE_PATH, "vector_dbs"),
    "cache": os.path.join(STORAGE_PATH, "cache"),
    "exports": os.path.join(STORAGE_PATH, "exports")
}

# Create directories if they don't exist
for path in DIRECTORIES.values():
    os.makedirs(path, exist_ok=True)

def format_bytes(bytes_value: int) -> str:
    """Convert bytes to human readable format."""
    if bytes_value == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = int(math.floor(math.log(bytes_value, 1024)))
    p = pow(1024, i)
    s = round(bytes_value / p, 2)
    return f"{s} {size_names[i]}"

def get_directory_size(path: str) -> int:
    """Calculate total size of directory in bytes."""
    total_size = 0
    try:
        for dirpath, dirnames, filenames in os.walk(path):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                try:
                    total_size += os.path.getsize(filepath)
                except OSError:
                    # File might not exist or be inaccessible
                    continue
    except Exception:
        total_size = 0
    return total_size

def get_file_count(path: str) -> int:
    """Count total number of files in directory."""
    count = 0
    try:
        for dirpath, dirnames, filenames in os.walk(path):
            count += len(filenames)
    except Exception:
        count = 0
    return count

@app.get("/")
def read_root():
    return {"service": "storage-service", "status": "running"}

@app.get("/overview", response_model=StorageOverviewResponse)
def get_storage_overview():
    total_size = 0
    total_files = 0
    
    directories_info = {}
    for name, path in DIRECTORIES.items():
        size = get_directory_size(path)
        file_count = get_file_count(path)
        exists = os.path.exists(path)
        
        directories_info[name] = StorageDirectoryInfo(
            path=path,
            size_bytes=size,
            size_formatted=format_bytes(size),
            file_count=file_count,
            exists=exists
        )
        
        total_size += size
        total_files += file_count
    
    return StorageOverviewResponse(
        total_size=total_size,
        total_size_formatted=format_bytes(total_size),
        total_files=total_files,
        directories=directories_info,
        last_updated=datetime.utcnow().isoformat()
    )

@app.get("/users/{user_id}", response_model=UserStorageInfo)
def get_user_storage(user_id: int):
    # In a real implementation, this would query the database for user storage info
    # For now, return mock data for demonstration
    return UserStorageInfo(
        user_id=user_id,
        email=f"user{user_id}@example.com",
        full_name=f"User {user_id}",
        is_active=True,
        storage={
            "documents": {"count": 5, "size_bytes": 10000000, "size_formatted": "10 MB"},
            "cache": {"count": 10, "size_bytes": 3000000, "size_formatted": "3 MB"},
            "vector_dbs": {"count": 5, "size_bytes": 50000000, "size_formatted": "50 MB"}
        }
    )

@app.get("/users", response_model=UserStorageResponse)
def get_all_user_storage():
    # In a real implementation, this would fetch all users' storage info
    # For now, return mock data
    return UserStorageResponse(
        users=[
            UserStorageInfo(
                user_id=1,
                email="demo@example.com",
                full_name="Demo User",
                is_active=True,
                storage={
                    "documents": {"count": 15, "size_bytes": 25000000, "size_formatted": "25 MB"},
                    "cache": {"count": 28, "size_bytes": 5000000, "size_formatted": "5 MB"},
                    "vector_dbs": {"count": 15, "size_bytes": 120000000, "size_formatted": "120 MB"}
                }
            ),
            UserStorageInfo(
                user_id=2,
                email="admin@example.com",
                full_name="Admin User",
                is_active=True,
                storage={
                    "documents": {"count": 23, "size_bytes": 45000000, "size_formatted": "45 MB"},
                    "cache": {"count": 35, "size_bytes": 8000000, "size_formatted": "8 MB"},
                    "vector_dbs": {"count": 23, "size_bytes": 180000000, "size_formatted": "180 MB"}
                }
            )
        ]
    )

@app.post("/cleanup/orphaned", response_model=CleanupResult)
def cleanup_orphaned_files():
    # In a real implementation, this would identify and clean files not linked to documents in DB
    # For now, return mock cleanup result
    return CleanupResult(
        success=True,
        cleaned_items=[
            CleanupItem(name="orphaned_files", count=5),
            CleanupItem(name="orphaned_directories", count=2)
        ],
        errors=[],
        message="Successfully cleaned up 5 orphaned files and 2 orphaned directories"
    )

@app.post("/cleanup/user/{user_id}", response_model=CleanupResult)
def cleanup_user_storage(user_id: int):
    # In a real implementation, this would clean up all storage for a specific user
    # For now, return mock result
    return CleanupResult(
        success=True,
        cleaned_items=[
            CleanupItem(name="user_documents", count=3),
            CleanupItem(name="cache_entries", count=7),
            CleanupItem(name="vector_dbs", count=3)
        ],
        errors=[],
        message=f"Successfully cleaned up storage for user {user_id}"
    )

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "storage-service"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)
from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import os
import shutil
import uuid
from datetime import datetime
import logging
from pathlib import Path

app = FastAPI(
    title="Storage Management Service",
    version="1.0.0",
    root_path="/storage"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StorageStats(BaseModel):
    total_size_bytes: int
    total_size_formatted: str
    total_files: int
    directories: Dict[str, Any]
    last_updated: str

class UserStorageInfo(BaseModel):
    user_id: int
    email: str
    full_name: Optional[str]
    storage_used_bytes: int
    storage_used_formatted: str
    file_count: int
    storage_limit_bytes: int
    storage_limit_formatted: str

# Configuration
STORAGE_PATH = os.environ.get("STORAGE_PATH", "/data/storage")
Path(STORAGE_PATH).mkdir(parents=True, exist_ok=True)

@app.get("/")
def read_root():
    return {"service": "storage-service", "status": "running"}

@app.post("/upload/{user_id}")
async def upload_file(user_id: int, file: UploadFile = File(...)):
    try:
        # Create user-specific directory
        user_dir = os.path.join(STORAGE_PATH, str(user_id))
        os.makedirs(user_dir, exist_ok=True)
        
        # Generate unique filename
        file_extension = Path(file.filename).suffix
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(user_dir, unique_filename)
        
        # Save file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        return {
            "filename": unique_filename,
            "original_filename": file.filename,
            "file_path": file_path,
            "file_size": os.path.getsize(file_path),
            "user_id": user_id
        }
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")

@app.get("/stats", response_model=StorageStats)
def get_storage_stats():
    total_size = 0
    total_files = 0
    
    directories = {}
    for dirpath, dirnames, filenames in os.walk(STORAGE_PATH):
        dir_size = 0
        file_count = 0
        
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            try:
                size = os.path.getsize(filepath)
                dir_size += size
                total_size += size
                file_count += 1
                total_files += 1
            except OSError:
                continue  # Skip files that can't be accessed
        
        relative_path = os.path.relpath(dirpath, STORAGE_PATH)
        if relative_path == '.':
            relative_path = 'root'
        
        directories[relative_path] = {
            "size_bytes": dir_size,
            "size_formatted": format_bytes(dir_size),
            "file_count": file_count
        }
    
    return StorageStats(
        total_size_bytes=total_size,
        total_size_formatted=format_bytes(total_size),
        total_files=total_files,
        directories=directories,
        last_updated=datetime.utcnow().isoformat()
    )

@app.get("/user/{user_id}", response_model=UserStorageInfo)
def get_user_storage(user_id: int):
    user_dir = os.path.join(STORAGE_PATH, str(user_id))
    
    if not os.path.exists(user_dir):
        return UserStorageInfo(
            user_id=user_id,
            email=f"user{user_id}@example.com",
            full_name=f"User {user_id}",
            storage_used_bytes=0,
            storage_used_formatted="0 B",
            file_count=0,
            storage_limit_bytes=1073741824,  # 1 GB
            storage_limit_formatted="1 GB"
        )
    
    total_size = 0
    file_count = 0
    
    for dirpath, dirnames, filenames in os.walk(user_dir):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            try:
                size = os.path.getsize(filepath)
                total_size += size
                file_count += 1
            except OSError:
                continue  # Skip files that can't be accessed
    
    return UserStorageInfo(
        user_id=user_id,
        email=f"user{user_id}@example.com", 
        full_name=f"User {user_id}",
        storage_used_bytes=total_size,
        storage_used_formatted=format_bytes(total_size),
        file_count=file_count,
        storage_limit_bytes=1073741824,  # 1 GB
        storage_limit_formatted="1 GB"
    )

@app.delete("/file/{user_id}/{filename}")
def delete_file(user_id: int, filename: str):
    file_path = os.path.join(STORAGE_PATH, str(user_id), filename)
    
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
            
            # Also remove the directory if it's empty
            user_dir = os.path.dirname(file_path)
            if not os.listdir(user_dir):  # Check if directory is empty
                os.rmdir(user_dir)
                
            return {"message": f"File {filename} deleted successfully"}
        except OSError as e:
            raise HTTPException(status_code=500, detail=f"Error deleting file: {str(e)}")
    else:
        raise HTTPException(status_code=404, detail="File not found")

def format_bytes(bytes_value: int) -> str:
    """Convert bytes to human readable format."""
    if bytes_value == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    import math
    i = int(math.floor(math.log(bytes_value, 1024)))
    p = math.pow(1024, i)
    s = round(bytes_value / p, 2)
    return f"{s} {size_names[i]}"

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "storage-service"}
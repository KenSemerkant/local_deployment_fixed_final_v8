from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict
import os
import shutil
import sqlite3
from datetime import datetime
import json

# OpenTelemetry tracing setup
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor

# Configure OpenTelemetry
otel_endpoint = os.getenv("OTEL_EXPORTER_OTLP_TRACES_ENDPOINT", "http://jaeger:4318/v1/traces")
service_name = os.getenv("OTEL_SERVICE_NAME", "storage_service")

# Set up the tracer
trace.set_tracer_provider(TracerProvider())
tracer = trace.get_tracer(__name__)

# Add OTLP span processor
span_processor = BatchSpanProcessor(
    OTLPSpanExporter(endpoint=otel_endpoint)
)
trace.get_tracer_provider().add_span_processor(span_processor)

# Initialize FastAPI app
app = FastAPI(title="Storage Service", version="1.0.0")

# Enable tracing for the FastAPI app
FastAPIInstrumentor.instrument_app(app)

# Instrument other libraries
RequestsInstrumentor().instrument()
LoggingInstrumentor().instrument()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
STORAGE_PATH = os.getenv("STORAGE_PATH", "/data")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./storage.db")

# MinIO configuration
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "minio:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
MINIO_SECURE = os.getenv("MINIO_SECURE", "false").lower() == "true"
DOCUMENTS_BUCKET = os.getenv("DOCUMENTS_BUCKET", "documents")

# Initialize MinIO client
from minio import Minio
minio_client = Minio(
    MINIO_ENDPOINT,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=MINIO_SECURE
)

# Verify bucket exists
if not minio_client.bucket_exists(DOCUMENTS_BUCKET):
    minio_client.make_bucket(DOCUMENTS_BUCKET)

class StorageOverviewResponse(BaseModel):
    total_size_bytes: int
    used_size_bytes: int
    free_size_bytes: int
    total_files: int
    file_types: Dict[str, int]

class UserStorageResponse(BaseModel):
    user_id: int
    total_size_bytes: int
    file_count: int
    files: List[Dict]

class StorageCleanupResult(BaseModel):
    cleaned_files_count: int
    freed_size_bytes: int
    message: str

def get_db_connection():
    """Create a database connection"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row  # Enable column access by name
    return conn

def create_tables():
    """Create required database tables"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stored_files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            file_path TEXT NOT NULL,
            file_size INTEGER NOT NULL,
            mime_type TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()

def get_directory_size(path):
    """Calculate the total size of a directory"""
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(path):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            if os.path.exists(filepath):
                total_size += os.path.getsize(filepath)
    return total_size

@app.on_event("startup")
def startup_event():
    """Initialize database tables on startup"""
    global DATABASE_PATH
    DATABASE_PATH = DATABASE_URL.replace("sqlite:///", "")
    create_tables()

@app.get("/")
def root():
    return {"message": "Storage Service", "version": "1.0.0"}

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "storage-service"}

@app.get("/admin/overview")
def get_storage_overview():
    """Get storage overview"""
    total_size = get_directory_size(STORAGE_PATH)
    total_files = 0
    file_types = {}

    for dirpath, dirnames, filenames in os.walk(STORAGE_PATH):
        for filename in filenames:
            total_files += 1
            _, ext = os.path.splitext(filename)
            ext = ext.lower()
            if ext in file_types:
                file_types[ext] += 1
            else:
                file_types[ext] = 1

    # Get MinIO storage statistics
    try:
        minio_objects = list(minio_client.list_objects(DOCUMENTS_BUCKET, recursive=True))
        minio_size = sum(obj.size for obj in minio_objects if obj.size)
        minio_count = len(minio_objects)

        # Add file types from MinIO if available
        for obj in minio_objects:
            _, ext = os.path.splitext(obj.object_name)
            ext = ext.lower()
            if ext in file_types:
                file_types[ext] += 1
            else:
                file_types[ext] = 1
    except Exception as e:
        minio_size = 0
        minio_count = 0
        print(f"Error getting MinIO stats: {e}")

    total_size += minio_size
    total_files += minio_count

    # Get available disk space
    statvfs = os.statvfs(STORAGE_PATH)
    free_size = statvfs.f_frsize * statvfs.f_bavail

    return {
        "total_size_bytes": total_size + free_size,
        "used_size_bytes": total_size,
        "free_size_bytes": free_size,
        "total_files": total_files,
        "file_types": file_types,
        "minio_stats": {
            "size_bytes": minio_size,
            "file_count": minio_count
        }
    }

@app.get("/admin/users")
def get_user_storage_details(user_id: Optional[int] = None):
    """Get user storage details"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if user_id:
        cursor.execute("""
            SELECT * FROM stored_files WHERE user_id = ?
            ORDER BY created_at DESC
        """, (user_id,))
    else:
        cursor.execute("SELECT * FROM stored_files ORDER BY created_at DESC")
    
    files = cursor.fetchall()
    conn.close()
    
    users_data = {}
    for file_row in files:
        uid = file_row["user_id"]
        if uid not in users_data:
            users_data[uid] = {
                "user_id": uid,
                "total_size_bytes": 0,
                "file_count": 0,
                "files": []
            }
        
        file_info = {
            "id": file_row["id"],
            "filename": file_row["filename"],
            "file_path": file_row["file_path"],
            "file_size": file_row["file_size"],
            "mime_type": file_row["mime_type"],
            "created_at": file_row["created_at"]
        }
        
        users_data[uid]["total_size_bytes"] += file_row["file_size"]
        users_data[uid]["file_count"] += 1
        users_data[uid]["files"].append(file_info)
    
    return {"users": list(users_data.values())}

@app.post("/admin/cleanup/user/{user_id}")
def cleanup_user_storage(user_id: int):
    """Clean up storage for a specific user"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Get files for the user
    cursor.execute("SELECT * FROM stored_files WHERE user_id = ?", (user_id,))
    files = cursor.fetchall()

    cleaned_files_count = 0
    freed_size_bytes = 0

    for file_row in files:
        file_path = file_row["file_path"]

        # Check if path is a local file or MinIO object
        if os.path.exists(file_path):
            # Local file - remove as before
            try:
                file_size = os.path.getsize(file_path)
                os.remove(file_path)
                freed_size_bytes += file_size
                cleaned_files_count += 1
            except Exception as e:
                print(f"Error deleting local file {file_path}: {e}")
        else:
            # Likely a MinIO object - try to delete from MinIO
            try:
                obj_stat = minio_client.stat_object(DOCUMENTS_BUCKET, file_path)
                minio_client.remove_object(DOCUMENTS_BUCKET, file_path)
                freed_size_bytes += obj_stat.size
                cleaned_files_count += 1
            except Exception as e:
                print(f"Error deleting MinIO object {file_path}: {e}")

    # Remove records from database
    cursor.execute("DELETE FROM stored_files WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

    return {
        "cleaned_files_count": cleaned_files_count,
        "freed_size_bytes": freed_size_bytes,
        "message": f"Cleaned up {cleaned_files_count} files for user {user_id}"
    }

@app.post("/admin/cleanup/orphaned")
def cleanup_orphaned_files():
    """Clean up orphaned files"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Get all files from database
    cursor.execute("SELECT * FROM stored_files")
    stored_files = cursor.fetchall()

    # Collect all file paths in DB
    db_file_paths = set()
    for file_row in stored_files:
        db_file_paths.add(file_row["file_path"])

    # Walk through storage directory to find local files not in DB
    orphaned_local_files = []
    for dirpath, dirnames, filenames in os.walk(STORAGE_PATH):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            if filepath not in db_file_paths:
                if os.path.isfile(filepath):  # Make sure it's a file
                    orphaned_local_files.append(filepath)

    # Find orphaned MinIO objects
    try:
        all_minio_objects = list(minio_client.list_objects(DOCUMENTS_BUCKET, recursive=True))
        orphaned_minio_objects = []
        for obj in all_minio_objects:
            if obj.object_name not in db_file_paths:
                orphaned_minio_objects.append(obj)
    except Exception as e:
        print(f"Error listing MinIO objects: {e}")
        orphaned_minio_objects = []

    # Remove orphaned local files
    cleaned_files_count = 0
    freed_size_bytes = 0

    for filepath in orphaned_local_files:
        try:
            file_size = os.path.getsize(filepath)
            os.remove(filepath)
            freed_size_bytes += file_size
            cleaned_files_count += 1
        except Exception as e:
            print(f"Error deleting orphaned local file {filepath}: {e}")

    # Remove orphaned MinIO objects
    for obj in orphaned_minio_objects:
        try:
            minio_client.remove_object(DOCUMENTS_BUCKET, obj.object_name)
            freed_size_bytes += obj.size
            cleaned_files_count += 1
        except Exception as e:
            print(f"Error deleting orphaned MinIO object {obj.object_name}: {e}")

    conn.close()

    return {
        "cleaned_files_count": cleaned_files_count,
        "freed_size_bytes": freed_size_bytes,
        "message": f"Cleaned up {cleaned_files_count} orphaned files"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
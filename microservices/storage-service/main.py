from fastapi import FastAPI, HTTPException, UploadFile, File, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict
import os
import shutil
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import json
import io

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

# Internal API Key configuration
INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY")

async def verify_internal_api_key(x_internal_api_key: str = Header(None)):
    if not INTERNAL_API_KEY:
        return
    if x_internal_api_key != INTERNAL_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid Internal API Key")

# Initialize FastAPI app
app = FastAPI(
    title="Storage Service", 
    version="1.0.0",
    dependencies=[Depends(verify_internal_api_key)]
)

# Enable tracing for the FastAPI app
FastAPIInstrumentor.instrument_app(app)

# Instrument other libraries
RequestsInstrumentor().instrument()
LoggingInstrumentor().instrument()

# CORS removed as this service is behind the gateway

# Configuration
STORAGE_PATH = os.getenv("STORAGE_PATH", "/data")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@postgres:5432/app_db")

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

AVATARS_BUCKET = os.getenv("AVATARS_BUCKET", "avatars")
if not minio_client.bucket_exists(AVATARS_BUCKET):
    minio_client.make_bucket(AVATARS_BUCKET)
    # Set policy to public read for avatars
    policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {"AWS": "*"},
                "Action": ["s3:GetObject"],
                "Resource": [f"arn:aws:s3:::{AVATARS_BUCKET}/*"]
            }
        ]
    }
    minio_client.set_bucket_policy(AVATARS_BUCKET, json.dumps(policy))

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
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    return conn

def create_tables():
    """Create required database tables"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stored_files (
                id SERIAL PRIMARY KEY,
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
    except Exception as e:
        print(f"Error creating tables: {e}")

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
    """Initialize database tables and storage directory on startup"""
    
    # Ensure storage directory exists
    if not os.path.exists(STORAGE_PATH):
        os.makedirs(STORAGE_PATH, exist_ok=True)
        
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
            SELECT * FROM stored_files WHERE user_id = %s
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
    cursor.execute("SELECT * FROM stored_files WHERE user_id = %s", (user_id,))
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
    cursor.execute("DELETE FROM stored_files WHERE user_id = %s", (user_id,))
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

@app.post("/admin/sync")
def sync_storage_metadata():
    """Synchronize storage metadata with actual files in MinIO"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    synced_count = 0
    
    try:
        # Get all objects from MinIO
        minio_objects = list(minio_client.list_objects(DOCUMENTS_BUCKET, recursive=True))
        
        for obj in minio_objects:
            # Check if file already exists in DB
            cursor.execute("SELECT id FROM stored_files WHERE file_path = %s", (obj.object_name,))
            existing = cursor.fetchone()
            
            if not existing:
                # Infer user_id from metadata or path if possible, otherwise default to 1 (admin)
                # In a real scenario, we'd need better metadata management
                # For now, we'll assume a default user or try to parse from path if it follows a pattern
                user_id = 1 
                
                # Insert into DB
                cursor.execute("""
                    INSERT INTO stored_files (filename, file_path, file_size, mime_type, user_id)
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    os.path.basename(obj.object_name),
                    obj.object_name,
                    obj.size,
                    "application/pdf", # Default to PDF for now
                    user_id
                ))
                synced_count += 1
        
        conn.commit()
        message = f"Synchronized {synced_count} new files from storage"
        
    except Exception as e:
        print(f"Error syncing storage: {e}")
        message = f"Error syncing storage: {str(e)}"
    finally:
        conn.close()
        
    return {"message": message, "synced_count": synced_count}

@app.post("/avatars/upload")
async def upload_avatar(file: UploadFile = File(...)):
    """Upload an avatar image"""
    try:
        # Validate file type
        if not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="File must be an image")
            
        # Generate unique filename
        ext = os.path.splitext(file.filename)[1]
        filename = f"{datetime.now().timestamp()}_{os.urandom(4).hex()}{ext}"
        
        # Read file content
        content = await file.read()
        file_size = len(content)
        
        # Upload to MinIO
        minio_client.put_object(
            AVATARS_BUCKET,
            filename,
            io.BytesIO(content),
            file_size,
            content_type=file.content_type
        )
        
        # Return the URL (relative or absolute depending on needs)
        # For now, return the filename, frontend can construct URL via gateway
        return {"filename": filename, "url": f"/storage/avatars/{filename}"}
        
    except Exception as e:
        print(f"Error uploading avatar: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to upload avatar: {str(e)}")

@app.get("/avatars/{filename}")
async def get_avatar(filename: str):
    """Get an avatar image"""
    try:
        # Get object from MinIO
        response = minio_client.get_object(AVATARS_BUCKET, filename)
        
        # Return as streaming response
        from fastapi.responses import StreamingResponse
        return StreamingResponse(
            response, 
            media_type=response.headers.get("content-type", "image/jpeg")
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail="Avatar not found")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
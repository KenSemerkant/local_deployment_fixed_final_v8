from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, BackgroundTasks, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import os
import shutil
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import json
import requests
from io import BytesIO
import logging

import redis
import json
import json
from rabbitmq import publish_message, get_queue_depth

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Redis configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
try:
    redis_client = redis.from_url(REDIS_URL, decode_responses=True)
except Exception as e:
    logger.error(f"Failed to connect to Redis: {e}")
    redis_client = None
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
service_name = os.getenv("OTEL_SERVICE_NAME", "document_service")

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
    title="Document Service", 
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

# Create bucket if it doesn't exist
if not minio_client.bucket_exists(DOCUMENTS_BUCKET):
    minio_client.make_bucket(DOCUMENTS_BUCKET)

# Service URLs
LLM_SERVICE_URL = os.getenv("LLM_SERVICE_URL", "http://llm-service:8000")
ANALYTICS_SERVICE_URL = os.getenv("ANALYTICS_SERVICE_URL", "http://analytics-service:8000")

# ... (MinIO config) ...

def track_analytics_event(user_id: int, event_type: str, event_data: dict):
    """Helper to track analytics events asynchronously"""
    print(f"DEBUG: Attempting to track event {event_type} to {ANALYTICS_SERVICE_URL}")
    try:
        headers = {}
        if INTERNAL_API_KEY:
            headers["X-Internal-API-Key"] = INTERNAL_API_KEY
            
        response = requests.post(
            f"{ANALYTICS_SERVICE_URL}/events",
            json={
                "user_id": user_id,
                "event_type": event_type,
                "event_data": event_data
            },
            headers=headers,
            timeout=5
        )
        print(f"DEBUG: Analytics response: {response.status_code} - {response.text}")
    except Exception as e:
        logger.error(f"Failed to track analytics event: {e}")
        print(f"DEBUG: Failed to track analytics event: {e}")

def track_performance_metric(user_id: int, metric_type: str, start_time: datetime, end_time: datetime, success: bool, error_message: str = None, document_id: int = None):
    """Helper to track performance metrics asynchronously"""
    try:
        headers = {}
        if INTERNAL_API_KEY:
            headers["X-Internal-API-Key"] = INTERNAL_API_KEY
            
        requests.post(
            f"{ANALYTICS_SERVICE_URL}/metrics",
            json={
                "user_id": user_id,
                "metric_type": metric_type,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "success": success,
                "error_message": error_message,
                "document_id": document_id
            },
            headers=headers,
            timeout=5
        )
    except Exception as e:
        print(f"Error tracking performance metric: {e}")

class DocumentResponse(BaseModel):
    id: int
    filename: str
    file_path: str
    file_size: int
    mime_type: str
    owner_id: int
    created_at: datetime
    updated_at: datetime
    status: str = "PROCESSING"

class AnalysisResultResponse(BaseModel):
    id: int
    summary: str
    key_figures: List[dict]
    created_at: datetime

class QuestionRequest(BaseModel):
    question: str

class QuestionResponse(BaseModel):
    id: int
    question_text: str
    answer_text: str
    sources: List[dict]
    created_at: datetime

class UpdateStepRequest(BaseModel):
    step: str

def get_db_connection():
    """Create a database connection"""
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    return conn

def migrate_database():
    """Migrate database schema to include new columns"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if columns exist in documents table
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='documents' AND column_name='error_message'
        """)
        if not cursor.fetchone():
            print("Migrating database: Adding error_message column")
            cursor.execute("ALTER TABLE documents ADD COLUMN error_message TEXT")
            
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='documents' AND column_name='processing_step'
        """)
        if not cursor.fetchone():
            print("Migrating database: Adding processing_step column")
            cursor.execute("ALTER TABLE documents ADD COLUMN processing_step TEXT")
            
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error migrating database: {e}")

def create_tables():
    """Create required database tables"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id SERIAL PRIMARY KEY,
                filename TEXT NOT NULL,
                file_path TEXT NOT NULL,
                file_size INTEGER NOT NULL,
                mime_type TEXT NOT NULL,
                owner_id INTEGER NOT NULL,
                status TEXT DEFAULT 'PROCESSING',
                error_message TEXT,
                processing_step TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS analysis_results (
                id SERIAL PRIMARY KEY,
                document_id INTEGER NOT NULL,
                summary TEXT NOT NULL,
                key_figures TEXT NOT NULL,
                vector_db_path TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (document_id) REFERENCES documents (id)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS qa_sessions (
                id SERIAL PRIMARY KEY,
                document_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (document_id) REFERENCES documents (id)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS questions (
                id SERIAL PRIMARY KEY,
                qa_session_id INTEGER NOT NULL,
                question_text TEXT NOT NULL,
                answer_text TEXT NOT NULL,
                sources TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (qa_session_id) REFERENCES qa_sessions (id)
            )
        """)
        
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error creating tables: {e}")

def update_document_step(document_id: int, step: str):
    """Update the processing step for a document"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE documents SET processing_step = %s WHERE id = %s",
            (step, document_id)
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error updating document step: {e}")

    # Invalidate cache so dashboard updates step
    if redis_client:
        try:
            # We don't have owner_id easily here without a DB lookup, 
            # but for demo we know it's likely 1. 
            # To be safe and efficient, we might skip this for every step 
            # OR do a quick lookup. For now, let's invalidate the demo key.
            redis_client.delete("documents_list:1")
        except Exception as e:
            logger.error(f"Redis delete error: {e}")

def process_document_task(document_id: int):
    """Background task to process a document and extract analysis"""
    start_time = datetime.utcnow()
    try:
        # Get document from database
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM documents WHERE id = %s", (document_id,))
        document = cursor.fetchone()
        conn.close()

        if not document:
            print(f"Document {document_id} not found")
            return

        minio_object_name = document["file_path"]

        # Update step
        update_document_step(document_id, "Sending to LLM service for analysis...")

        # Call LLM service for processing, sending the MinIO object name and callback info
        try:
            # Determine callback URL (assuming document-service is reachable by llm-service)
            # In docker-compose, service name is 'document-service'
            callback_url = f"http://document-service:8000/documents/{document_id}/step"
            
            headers = {}
            if INTERNAL_API_KEY:
                headers["X-Internal-API-Key"] = INTERNAL_API_KEY

            llm_response = requests.post(
                f"{LLM_SERVICE_URL}/analyze",
                json={
                    "document_path": minio_object_name,
                    "document_id": document_id,
                    "callback_url": callback_url
                },
                headers=headers,
                timeout=300
            )
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to connect to LLM service: {str(e)}")

        if llm_response.status_code != 200:
            error_detail = "Unknown error from LLM service"
            try:
                error_detail = llm_response.json().get("detail", llm_response.text)
            except:
                error_detail = llm_response.text
            raise Exception(f"LLM service error ({llm_response.status_code}): {error_detail}")

        update_document_step(document_id, "Processing LLM response...")
        result = llm_response.json()

        # Store the result in analysis_results table
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO analysis_results (document_id, summary, key_figures, vector_db_path)
            VALUES (%s, %s, %s, %s)
        """, (
            document_id,
            result.get("summary", ""),
            json.dumps(result.get("key_figures", [])),
            result.get("vector_db_path", "")
        ))

        # Update document status to 'COMPLETED'
        cursor.execute(
            "UPDATE documents SET status = %s, processing_step = %s, error_message = NULL WHERE id = %s",
            ("COMPLETED", "Completed", document_id)
        )

        conn.commit()
        conn.close()

        # Track analysis event
        token_usage = result.get("token_usage", {})
        print(f"DEBUG: Token usage received from LLM service for analysis: {token_usage}")
        
        track_analytics_event(
            user_id=document["owner_id"],
            event_type="document_analyzed",
            event_data={
                "document_id": document_id,
                "file_size": document["file_size"],
                "token_usage": token_usage
            }
        )
        
        # Track performance metric
        end_time = datetime.utcnow()
        track_performance_metric(
            user_id=document["owner_id"],
            metric_type="document_processing",
            start_time=start_time,
            end_time=end_time,
            success=True,
            document_id=document_id
        )

        print(f"Document {document_id} processed successfully")
        
        # Invalidate cache so dashboard updates status
        if redis_client:
            try:
                redis_client.delete(f"documents_list:{document['owner_id']}")
                # Also delete the generic one for demo if used
                redis_client.delete("documents_list:1")
            except Exception as e:
                logger.error(f"Redis delete error: {e}")
    except Exception as e:
        print(f"Error processing document {document_id}: {e}")
        
        # Track failed performance metric
        end_time = datetime.utcnow()
        # Need user_id, try to get it if document was loaded
        user_id = 0 # Default if document load failed
        try:
            if 'document' in locals() and document:
                user_id = document["owner_id"]
        except:
            pass
            
        track_performance_metric(
            user_id=user_id,
            metric_type="document_processing",
            start_time=start_time,
            end_time=end_time,
            success=False,
            error_message=str(e),
            document_id=document_id
        )

        # Update document status to 'ERROR'
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE documents SET status = %s, error_message = %s, processing_step = %s WHERE id = %s",
                ("ERROR", str(e), "Failed", document_id)
            )
            conn.commit()
            conn.close()
        except Exception as update_error:
            print(f"Error updating document status: {update_error}")
            
        # Invalidate cache so dashboard updates status
        if redis_client:
            try:
                # Try to get owner_id if possible
                owner_id = 1
                if 'document' in locals() and document:
                    owner_id = document["owner_id"]
                
                redis_client.delete(f"documents_list:{owner_id}")
                redis_client.delete("documents_list:1")
            except Exception as e:
                logger.error(f"Redis delete error: {e}")

@app.on_event("startup")
def startup_event():
    """Initialize database tables on startup"""
    create_tables()
    migrate_database()

@app.get("/")
def root():
    return {"message": "Document Service", "version": "1.0.0"}

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "document-service", "dependencies": ["llm-service"]}

@app.post("/documents")
async def upload_document(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    # Reset file pointer to beginning
    await file.seek(0)

    # Read file content
    file_content = await file.read()
    file_size = len(file_content)

    # Generate a unique object name for MinIO
    import uuid
    object_name = f"{uuid.uuid4()}/{file.filename}"

    # Upload file to MinIO
    try:
        file_data = BytesIO(file_content)
        minio_client.put_object(
            DOCUMENTS_BUCKET,
            object_name,
            file_data,
            file_size,
            content_type=file.content_type
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not save file to MinIO: {str(e)}")

    # Create document in database
    conn = get_db_connection()
    cursor = conn.cursor()

    # Store the MinIO object name instead of a local path
    cursor.execute("""
        INSERT INTO documents (filename, file_path, file_size, mime_type, owner_id)
        VALUES (%s, %s, %s, %s, %s) RETURNING id
    """, (file.filename, object_name, file_size, file.content_type, 1))  # Assuming owner_id = 1 for demo

    document_id = cursor.fetchone()['id']
    conn.commit()
    conn.close()

    # Process document via RabbitMQ
    message = {"document_id": document_id, "action": "process_document"}
    if publish_message(message):
        logger.info(f"Queued document {document_id} for processing")
        # Update step to indicate queued status
        # We can't use update_document_step here easily without circular imports or code duplication
        # But the default status is PROCESSING, which is fine.
    else:
        logger.error(f"Failed to queue document {document_id}")
        # Fallback to background task if RabbitMQ fails? 
        # For now, let's keep it simple and just log error, or maybe fallback.
        # Let's fallback to background task for robustness during migration
        logger.warning("Falling back to local background task")
        background_tasks.add_task(process_document_task, document_id)

    # Track upload event
    background_tasks.add_task(
        track_analytics_event,
        user_id=1, # TODO: Get from auth context
        event_type="document_uploaded",
        event_data={
            "document_id": document_id,
            "file_size": file_size,
            "mime_type": file.content_type
        }
    )

    # Return document info
    # Invalidate cache
    if redis_client:
        try:
            redis_client.delete("documents_list:1")
        except Exception as e:
            logger.error(f"Redis delete error: {e}")

    return {
        "id": document_id,
        "filename": file.filename,
        "file_path": object_name,  # This is now the MinIO object name
        "file_size": file_size,
        "mime_type": file.content_type,
        "owner_id": 1,
        "status": "PROCESSING"
    }

@app.patch("/documents/{document_id}/step")
def update_document_step_endpoint(document_id: int, request: UpdateStepRequest):
    """Update the processing step of a document (called by LLM service)"""
    update_document_step(document_id, request.step)
    return {"message": "Step updated successfully"}

class UploadUrlRequest(BaseModel):
    url: str
    owner_id: int = 1  # Default to admin for now

@app.post("/documents/upload-url", response_model=DocumentResponse)
async def upload_document_from_url(
    request: UploadUrlRequest,
    background_tasks: BackgroundTasks
):
    """
    Upload a document from a URL.
    Supports PDF and HTML (converts to PDF).
    """
    logger.info(f"Received URL upload request: {request.url}")
    
    try:
        # 1. Fetch URL content
        import requests
        from urllib.parse import urlparse
        
        # Fetch the content from the URL
        # Use a comprehensive set of headers to mimic a real browser and avoid 403 Forbidden
        # SEC.gov specifically requires a User-Agent in the format "Name <email>"
        headers = {
            'User-Agent': 'FinancialAnalysisAgent admin@example.com',
            'Accept-Encoding': 'gzip, deflate',
            'Host': 'www.sec.gov'
        }
        response = requests.get(request.url, headers=headers, timeout=30)
        response.raise_for_status()
        
        content_type = response.headers.get("Content-Type", "").lower()
        parsed_url = urlparse(request.url)
        filename = parsed_url.path.split('/')[-1] or "document.pdf"
        
        if not filename.lower().endswith(('.pdf', '.html', '.htm')):
            if "pdf" in content_type:
                filename += ".pdf"
            elif "html" in content_type:
                filename += ".html"
            else:
                # Default to PDF if unknown
                filename += ".pdf"

        # 2. Process Content
        file_content = response.content
        final_filename = filename
        
        if "html" in content_type or filename.lower().endswith(('.html', '.htm')):
            # Convert HTML to PDF
            logger.info("Converting HTML to PDF...")
            try:
                from weasyprint import HTML
                import io
                
                pdf_bytes = HTML(string=response.text, base_url=request.url).write_pdf()
                file_content = pdf_bytes
                final_filename = filename.rsplit('.', 1)[0] + ".pdf"
                content_type = "application/pdf"
            except ImportError:
                logger.error("WeasyPrint not installed. Please install with 'pip install weasyprint'")
                raise HTTPException(status_code=500, detail="HTML conversion not supported (WeasyPrint missing)")
            except Exception as e:
                logger.error(f"HTML conversion failed: {e}")
                raise HTTPException(status_code=500, detail=f"HTML conversion failed: {e}")

        # 3. Upload to MinIO
        file_size = len(file_content)
        import uuid
        unique_id = str(uuid.uuid4())
        file_path = f"{unique_id}/{final_filename}"
        
        try:
            import io
            minio_client.put_object(
                DOCUMENTS_BUCKET,
                file_path,
                io.BytesIO(file_content),
                file_size,
                content_type=content_type
            )
        except Exception as e:
            logger.error(f"Failed to upload to MinIO: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to upload to storage: {e}")

        # 4. Create DB Record
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO documents (filename, file_path, file_size, mime_type, owner_id, status)
            VALUES (%s, %s, %s, %s, %s, %s) RETURNING id
        """, (final_filename, file_path, file_size, content_type, request.owner_id, "UPLOADED"))
        
        document_id = cursor.fetchone()['id']
        conn.commit()
        
        # Fetch the created document to return it
        cursor.execute("SELECT * FROM documents WHERE id = %s", (document_id,))
        db_document = cursor.fetchone()
        conn.close()

        # 5. Trigger Analysis via RabbitMQ
        message = {"document_id": document_id, "action": "process_document"}
        if publish_message(message):
            logger.info(f"Queued document {document_id} for processing")
        else:
            logger.error(f"Failed to queue document {document_id}")
            logger.warning("Falling back to local background task")
            background_tasks.add_task(process_document_task, document_id)
        
        # Invalidate cache
        if redis_client:
            try:
                redis_client.delete("documents_list:1")
            except Exception as e:
                logger.error(f"Redis delete error: {e}")

        return {
            "id": db_document["id"],
            "filename": db_document["filename"],
            "file_path": db_document["file_path"],
            "file_size": db_document["file_size"],
            "mime_type": db_document["mime_type"],
            "owner_id": db_document["owner_id"],
            "created_at": db_document["created_at"],
            "updated_at": db_document["updated_at"],
            "status": db_document["status"]
        }
        
    except requests.RequestException as e:
        logger.error(f"Failed to fetch URL: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to fetch URL: {e}")
    except Exception as e:
        logger.error(f"URL upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"URL upload failed: {e}")

@app.post("/documents/upload", response_model=DocumentResponse)
def dummy_endpoint_for_response_model_definition():
    # This endpoint is a placeholder to satisfy the DocumentResponse model requirement
    # in the user's provided snippet. It will not be called.
    # The actual /documents endpoint already exists and returns a dict.
    # If the user intends to use DocumentResponse for /documents, that endpoint needs modification.
    pass

@app.get("/queue-status")
def get_queue_status():
    """Get current queue status metrics"""
    # 1. Get Queued count from RabbitMQ
    queued_count = get_queue_depth()
    
    # 2. Get Processing and Completed counts from DB
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Processing count
    cursor.execute("SELECT COUNT(*) as count FROM documents WHERE status = 'PROCESSING'")
    processing_count = cursor.fetchone()["count"]
    
    # Completed in last 24h
    cursor.execute("""
        SELECT COUNT(*) as count 
        FROM documents 
        WHERE status = 'COMPLETED' 
        AND updated_at >= NOW() - INTERVAL '1 day'
    """)
    completed_24h_count = cursor.fetchone()["count"]
    
    # Get recently processed documents (last 5)
    cursor.execute("""
        SELECT id, filename, status, updated_at 
        FROM documents 
        WHERE status IN ('COMPLETED', 'ERROR')
        ORDER BY updated_at DESC 
        LIMIT 5
    """)
    recent_docs = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    
    return {
        "queued": queued_count,
        "processing": processing_count,
        "completed_24h": completed_24h_count,
        "recent_documents": recent_docs
    }

@app.get("/documents")
def list_documents():
    # Check Redis cache first
    # Since we don't have user_id in context yet (demo mode), we'll use a global key or hardcoded user_id=1
    # In a real app, we would use `documents_list:{user_id}`
    cache_key = "documents_list:1" 
    
    if redis_client:
        try:
            cached_docs = redis_client.get(cache_key)
            if cached_docs:
                return json.loads(cached_docs)
        except Exception as e:
            logger.error(f"Redis error: {e}")

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM documents")
    documents = cursor.fetchall()
    conn.close()
    
    result = []
    for doc in documents:
        result.append({
            "id": doc["id"],
            "filename": doc["filename"],
            "file_path": doc["file_path"],
            "file_size": doc["file_size"],
            "mime_type": doc["mime_type"],
            "owner_id": doc["owner_id"],
            "status": doc["status"],
            "created_at": doc["created_at"].isoformat() if doc["created_at"] else None,
            "updated_at": doc["updated_at"].isoformat() if doc["updated_at"] else None
        })
    
    # Cache result
    if redis_client:
        try:
            redis_client.setex(
                cache_key,
                300,  # 5 minutes TTL
                json.dumps(result)
            )
        except Exception as e:
            logger.error(f"Redis set error: {e}")

    return result

@app.get("/documents/{document_id}")
def get_document(document_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM documents WHERE id = %s", (document_id,))
    document = cursor.fetchone()
    # Fetch analysis result if available
    cursor.execute("SELECT * FROM analysis_results WHERE document_id = %s", (document_id,))
    analysis = cursor.fetchone()
    conn.close()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    response = {
        "id": document["id"],
        "filename": document["filename"],
        "file_path": document["file_path"],
        "file_size": document["file_size"],
        "mime_type": document["mime_type"],
        "owner_id": document["owner_id"],
        "status": document["status"],
        "error_message": document["error_message"] if "error_message" in document.keys() else None,
        "processing_step": document["processing_step"] if "processing_step" in document.keys() else None,
        "created_at": document["created_at"],
        "updated_at": document["updated_at"]
    }

    if analysis:
        response["analysis_results"] = {
            "summary": analysis["summary"],
            "key_figures": analysis["key_figures"]
        }
    
    return response

@app.delete("/documents/{document_id}")
def delete_document(document_id: int, background_tasks: BackgroundTasks):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Get file path (which is now the MinIO object name) to delete the actual file
    cursor.execute("SELECT file_path FROM documents WHERE id = %s", (document_id,))
    result = cursor.fetchone()

    if not result:
        raise HTTPException(status_code=404, detail="Document not found")

    minio_object_name = result["file_path"]

    # Delete from database
    cursor.execute("DELETE FROM documents WHERE id = %s", (document_id,))
    conn.commit()
    conn.close()

    # Delete from MinIO
    try:
        minio_client.remove_object(DOCUMENTS_BUCKET, minio_object_name)
    except Exception as e:
        # Log the error but don't fail the entire operation if MinIO deletion fails
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error deleting object {minio_object_name} from MinIO: {str(e)}")

    # Track deletion event
    background_tasks.add_task(
        track_analytics_event,
        user_id=1, # TODO: Get from auth context
        event_type="document_deleted",
        event_data={"document_id": document_id}
    )

    # Invalidate cache
    if redis_client:
        try:
            redis_client.delete("documents_list:1")
        except Exception as e:
            logger.error(f"Redis delete error: {e}")

    return {"message": "Document deleted successfully"}

@app.get("/documents/{document_id}/analysis")
def get_document_analysis(document_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM analysis_results WHERE document_id = ?", (document_id,))
    analysis_result = cursor.fetchone()
    conn.close()
    
    if not analysis_result:
        raise HTTPException(status_code=404, detail="Analysis result not found")
    
    try:
        key_figures = json.loads(analysis_result["key_figures"])
    except:
        key_figures = []
    
    return {
        "id": analysis_result["id"],
        "summary": analysis_result["summary"],
        "key_figures": key_figures,
        "created_at": analysis_result["created_at"]
    }

@app.post("/documents/{document_id}/ask")
def ask_document_question(document_id: int, question_request: QuestionRequest, background_tasks: BackgroundTasks):
    # First get the analysis result to get the vector DB path
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM analysis_results WHERE document_id = ?", (document_id,))
    analysis_result = cursor.fetchone()
    
    if not analysis_result:
        conn.close()
        raise HTTPException(status_code=404, detail="Analysis result not found")
    
    # Get document file path (MinIO object name)
    cursor.execute("SELECT file_path FROM documents WHERE id = ?", (document_id,))
    document = cursor.fetchone()
    conn.close()
    
    if not document:
        conn.close()
        raise HTTPException(status_code=404, detail="Document not found")
        
    document_path = document["file_path"]
    vector_db_path = analysis_result["vector_db_path"]
    
    # Call LLM service for Q&A
    try:
        headers = {}
        if INTERNAL_API_KEY:
            headers["X-Internal-API-Key"] = INTERNAL_API_KEY

        llm_response = requests.post(
            f"{LLM_SERVICE_URL}/ask",
            json={
                "document_path": document_path,
                "question": question_request.question,
                "vector_db_path": vector_db_path
            },
            headers=headers,
            timeout=300
        )
        
        if llm_response.status_code != 200:
            raise HTTPException(status_code=500, detail="Error from LLM service")
        
        result = llm_response.json()
        
        # Save the question and answer to the database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Create a QA session if one doesn't exist
        cursor.execute("SELECT id FROM qa_sessions WHERE document_id = ?", (document_id,))
        session = cursor.fetchone()
        if not session:
            cursor.execute("INSERT INTO qa_sessions (document_id) VALUES (?)", (document_id,))
            session_id = cursor.lastrowid
        else:
            session_id = session["id"]
        
        # Save the question
        cursor.execute("""
            INSERT INTO questions (qa_session_id, question_text, answer_text, sources)
            VALUES (?, ?, ?, ?)
        """, (session_id, question_request.question, result["answer"], json.dumps(result["sources"])))
        
        question_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Return the result
        try:
            sources = json.loads(result["sources"])
        except:
            sources = []
        
        # Track analytics event
        token_usage = result.get("token_usage", {})
        print(f"DEBUG: Token usage received from LLM service: {token_usage}")
        
        background_tasks.add_task(
            track_analytics_event,
            user_id=1, # TODO: Get from auth context
            event_type="question_asked",
            event_data={
                "document_id": document_id,
                "question_length": len(question_request.question),
                "answer_length": len(result["answer"]),
                "processing_time": 0, # Could track actual time
                "token_usage": token_usage
            }
        )

        return {
            "id": question_id,
            "question_text": question_request.question,
            "answer_text": result["answer"],
            "sources": sources,
            "created_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error asking question: {str(e)}")

@app.get("/documents/{document_id}/questions")
def list_document_questions(document_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT q.* FROM questions q
        JOIN qa_sessions s ON q.qa_session_id = s.id
        WHERE s.document_id = ?
    """, (document_id,))
    
    questions = cursor.fetchall()
    conn.close()
    
    result = []
    for question in questions:
        try:
            sources = json.loads(question["sources"])
        except:
            sources = []
        
        result.append({
            "id": question["id"],
            "question_text": question["question_text"],
            "answer_text": question["answer_text"],
            "sources": sources,
            "created_at": question["created_at"]
        })
    
    return result

@app.get("/documents/{document_id}/download")
def download_document(document_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM documents WHERE id = ?", (document_id,))
    document = cursor.fetchone()
    conn.close()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Document file_path now contains the MinIO object name
    minio_object_name = document["file_path"]
    filename = document["filename"]
    
    # Ensure filename is clean (remove any path components if present)
    if "/" in filename:
        filename = filename.split("/")[-1]
    if "\\" in filename:
        filename = filename.split("\\")[-1]

    # Download from MinIO to a temporary location and return
    import tempfile
    import os
    from fastapi.responses import FileResponse

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1]) as tmp_file:
            minio_client.fget_object(DOCUMENTS_BUCKET, minio_object_name, tmp_file.name)
            temp_file_path = tmp_file.name

        return FileResponse(
            temp_file_path,
            filename=filename,
            media_type='application/pdf',
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not download file from MinIO: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
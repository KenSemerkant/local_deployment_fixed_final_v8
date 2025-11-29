from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import os
import shutil
import sqlite3
from datetime import datetime
import json
import requests
from io import BytesIO
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
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

# Initialize FastAPI app
app = FastAPI(title="Document Service", version="1.0.0")

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
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./documents.db")
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

# LLM Service URL
LLM_SERVICE_URL = os.getenv("LLM_SERVICE_URL", "http://llm-service:8000")

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
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row  # Enable column access by name
    return conn

def migrate_database():
    """Migrate database schema to include new columns"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if columns exist in documents table
    cursor.execute("PRAGMA table_info(documents)")
    columns = [info[1] for info in cursor.fetchall()]
    
    if "error_message" not in columns:
        print("Migrating database: Adding error_message column")
        cursor.execute("ALTER TABLE documents ADD COLUMN error_message TEXT")
        
    if "processing_step" not in columns:
        print("Migrating database: Adding processing_step column")
        cursor.execute("ALTER TABLE documents ADD COLUMN processing_step TEXT")
        
    conn.commit()
    conn.close()

def create_tables():
    """Create required database tables"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
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
    
    # ... (rest of create_tables remains the same, but I need to be careful not to delete it)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS analysis_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
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
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (document_id) REFERENCES documents (id)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
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

def update_document_step(document_id: int, step: str):
    """Update the processing step for a document"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE documents SET processing_step = ? WHERE id = ?",
            (step, document_id)
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error updating document step: {e}")

def process_document_task(document_id: int):
    """Background task to process a document and extract analysis"""
    try:
        # Get document from database
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM documents WHERE id = ?", (document_id,))
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
            
            llm_response = requests.post(
                f"{LLM_SERVICE_URL}/analyze",
                json={
                    "document_path": minio_object_name,
                    "document_id": document_id,
                    "callback_url": callback_url
                },
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
            VALUES (?, ?, ?, ?)
        """, (
            document_id,
            result.get("summary", ""),
            json.dumps(result.get("key_figures", [])),
            result.get("vector_db_path", "")
        ))

        # Update document status to 'COMPLETED'
        cursor.execute(
            "UPDATE documents SET status = ?, processing_step = ?, error_message = NULL WHERE id = ?",
            ("COMPLETED", "Completed", document_id)
        )

        conn.commit()
        conn.close()

        print(f"Document {document_id} processed successfully")
    except Exception as e:
        print(f"Error processing document {document_id}: {e}")

        # Update document status to 'ERROR'
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE documents SET status = ?, error_message = ?, processing_step = ? WHERE id = ?",
                ("ERROR", str(e), "Failed", document_id)
            )
            conn.commit()
            conn.close()
        except Exception as update_error:
            print(f"Error updating document status: {update_error}")

@app.on_event("startup")
def startup_event():
    """Initialize database tables on startup"""
    # Extract path from DATABASE_URL
    global DATABASE_PATH
    DATABASE_PATH = DATABASE_URL.replace("sqlite:///", "")
    
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
        VALUES (?, ?, ?, ?, ?)
    """, (file.filename, object_name, file_size, file.content_type, 1))  # Assuming owner_id = 1 for demo

    document_id = cursor.lastrowid
    conn.commit()
    conn.close()

    # Process document in background
    background_tasks.add_task(process_document_task, document_id)

    # Return document info
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
        # 4. Create DB Record
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO documents (filename, file_path, file_size, mime_type, owner_id, status)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (final_filename, file_path, file_size, content_type, request.owner_id, "UPLOADED"))
        
        document_id = cursor.lastrowid
        conn.commit()
        
        # Fetch the created document to return it
        cursor.execute("SELECT * FROM documents WHERE id = ?", (document_id,))
        db_document = cursor.fetchone()
        conn.close()

        # 5. Trigger Analysis
        background_tasks.add_task(process_document_task, document_id)
        
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

@app.get("/documents")
def list_documents():
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
            "created_at": doc["created_at"],
            "updated_at": doc["updated_at"]
        })
    
    return result

@app.get("/documents/{document_id}")
def get_document(document_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM documents WHERE id = ?", (document_id,))
    document = cursor.fetchone()
    conn.close()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return {
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

@app.delete("/documents/{document_id}")
def delete_document(document_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Get file path (which is now the MinIO object name) to delete the actual file
    cursor.execute("SELECT file_path FROM documents WHERE id = ?", (document_id,))
    result = cursor.fetchone()

    if not result:
        raise HTTPException(status_code=404, detail="Document not found")

    minio_object_name = result["file_path"]

    # Delete from database
    cursor.execute("DELETE FROM documents WHERE id = ?", (document_id,))
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
def ask_document_question(document_id: int, question_request: QuestionRequest):
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
        llm_response = requests.post(
            f"{LLM_SERVICE_URL}/ask",
            json={
                "document_path": document_path,
                "question": question_request.question,
                "vector_db_path": vector_db_path
            },
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
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import os
import sqlite3
from datetime import datetime, timedelta
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
service_name = os.getenv("OTEL_SERVICE_NAME", "analytics_service")

# Set up the tracer
trace.set_tracer_provider(TracerProvider())
tracer = trace.get_tracer(__name__)

# Add OTLP span processor
span_processor = BatchSpanProcessor(
    OTLPSpanExporter(endpoint=otel_endpoint)
)
trace.get_tracer_provider().add_span_processor(span_processor)

# Initialize FastAPI app
app = FastAPI(title="Analytics Service", version="1.0.0")

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
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./analytics.db")

class FeedbackRequest(BaseModel):
    feedback_type: str
    rating: Optional[int] = None
    comment: Optional[str] = None
    helpful: Optional[bool] = None
    question_id: Optional[int] = None
    document_id: Optional[int] = None

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
        CREATE TABLE IF NOT EXISTS analytics_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            event_type TEXT NOT NULL,
            event_data TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS performance_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            metric_type TEXT NOT NULL,
            start_time TIMESTAMP NOT NULL,
            end_time TIMESTAMP NOT NULL,
            success BOOLEAN NOT NULL,
            error_message TEXT,
            document_id INTEGER,
            question_id INTEGER,
            file_size_bytes INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS token_usage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            model_name TEXT NOT NULL,
            prompt_tokens INTEGER DEFAULT 0,
            completion_tokens INTEGER DEFAULT 0,
            total_tokens INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            feedback_type TEXT NOT NULL,
            rating INTEGER,
            comment TEXT,
            helpful BOOLEAN,
            question_id INTEGER,
            document_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()

def track_analytics_event(user_id: int, event_type: str, event_data: Dict[str, Any]):
    """Track an analytics event"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO analytics_events (user_id, event_type, event_data)
        VALUES (?, ?, ?)
    """, (user_id, event_type, json.dumps(event_data)))
    
    conn.commit()
    conn.close()

def track_performance_metric(
    user_id: int, 
    metric_type: str, 
    start_time: datetime, 
    end_time: datetime, 
    success: bool,
    error_message: Optional[str] = None,
    document_id: Optional[int] = None,
    question_id: Optional[int] = None,
    file_size_bytes: Optional[int] = None
):
    """Track a performance metric"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO performance_metrics 
        (user_id, metric_type, start_time, end_time, success, error_message, document_id, question_id, file_size_bytes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id, metric_type, start_time, end_time, success, error_message, 
        document_id, question_id, file_size_bytes
    ))
    
    conn.commit()
    conn.close()

def track_token_usage(
    user_id: int, 
    model_name: str, 
    prompt_tokens: int = 0, 
    completion_tokens: int = 0, 
    total_tokens: int = 0
):
    """Track token usage"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO token_usage (user_id, model_name, prompt_tokens, completion_tokens, total_tokens)
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, model_name, prompt_tokens, completion_tokens, total_tokens))
    
    conn.commit()
    conn.close()

def track_user_feedback(
    user_id: int,
    feedback_type: str,
    rating: Optional[int] = None,
    comment: Optional[str] = None,
    helpful: Optional[bool] = None,
    question_id: Optional[int] = None,
    document_id: Optional[int] = None
):
    """Track user feedback"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO user_feedback 
        (user_id, feedback_type, rating, comment, helpful, question_id, document_id)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (user_id, feedback_type, rating, comment, helpful, question_id, document_id))
    
    conn.commit()
    conn.close()

@app.on_event("startup")
def startup_event():
    """Initialize database tables on startup"""
    global DATABASE_PATH
    DATABASE_PATH = DATABASE_URL.replace("sqlite:///", "")
    create_tables()

@app.get("/")
def root():
    return {"message": "Analytics Service", "version": "1.0.0"}

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "analytics-service"}

@app.get("/admin/overview")
def get_analytics_overview(days: int = 30):
    """Get analytics overview"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Calculate date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Get total events
    cursor.execute("""
        SELECT COUNT(*) as total_events FROM analytics_events 
        WHERE created_at >= ?
    """, (start_date.isoformat(),))
    total_events = cursor.fetchone()["total_events"]
    
    # Get total performance metrics
    cursor.execute("""
        SELECT COUNT(*) as total_metrics FROM performance_metrics 
        WHERE created_at >= ?
    """, (start_date.isoformat(),))
    total_metrics = cursor.fetchone()["total_metrics"]
    
    # Get total token usage
    cursor.execute("""
        SELECT SUM(total_tokens) as total_tokens FROM token_usage 
        WHERE created_at >= ?
    """, (start_date.isoformat(),))
    token_row = cursor.fetchone()
    total_tokens = token_row["total_tokens"] or 0
    
    # Get feedback count
    cursor.execute("""
        SELECT COUNT(*) as feedback_count FROM user_feedback 
        WHERE created_at >= ?
    """, (start_date.isoformat(),))
    feedback_count = cursor.fetchone()["feedback_count"]
    
    conn.close()
    
    return {
        "days": days,
        "total_events": total_events,
        "total_metrics": total_metrics,
        "total_tokens": total_tokens,
        "feedback_count": feedback_count,
        "overview_date_range": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat()
        }
    }

@app.get("/admin/usage-patterns")
def get_usage_patterns(days: int = 30):
    """Get usage patterns"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Calculate date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Get events by type
    cursor.execute("""
        SELECT event_type, COUNT(*) as count 
        FROM analytics_events 
        WHERE created_at >= ? 
        GROUP BY event_type
    """, (start_date.isoformat(),))
    
    events_by_type = [{"event_type": row["event_type"], "count": row["count"]} for row in cursor.fetchall()]
    
    conn.close()
    
    return {
        "days": days,
        "events_by_type": events_by_type
    }

@app.get("/admin/tokens")
def get_token_analytics(days: int = 30):
    """Get token usage analytics"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Calculate date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Get token usage by model
    cursor.execute("""
        SELECT model_name, SUM(total_tokens) as total_tokens, 
               SUM(prompt_tokens) as total_prompt_tokens,
               SUM(completion_tokens) as total_completion_tokens
        FROM token_usage 
        WHERE created_at >= ? 
        GROUP BY model_name
    """, (start_date.isoformat(),))
    
    token_usage_by_model = [
        {
            "model_name": row["model_name"],
            "total_tokens": row["total_tokens"],
            "total_prompt_tokens": row["total_prompt_tokens"],
            "total_completion_tokens": row["total_completion_tokens"]
        }
        for row in cursor.fetchall()
    ]
    
    # Get total token usage
    cursor.execute("""
        SELECT SUM(total_tokens) as grand_total_tokens FROM token_usage 
        WHERE created_at >= ?
    """, (start_date.isoformat(),))
    grand_total = cursor.fetchone()["grand_total_tokens"] or 0
    
    conn.close()
    
    return {
        "days": days,
        "grand_total_tokens": grand_total,
        "token_usage_by_model": token_usage_by_model
    }

@app.get("/admin/performance")
def get_performance_analytics(days: int = 30):
    """Get performance analytics"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Calculate date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Get average response times by metric type
    cursor.execute("""
        SELECT metric_type,
               AVG((julianday(end_time) - julianday(start_time)) * 24 * 60 * 60) as avg_duration_seconds,
               COUNT(*) as total_calls,
               SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful_calls
        FROM performance_metrics 
        WHERE created_at >= ? 
        GROUP BY metric_type
    """, (start_date.isoformat(),))
    
    performance_by_type = [
        {
            "metric_type": row["metric_type"],
            "avg_duration_seconds": round(row["avg_duration_seconds"], 2),
            "total_calls": row["total_calls"],
            "successful_calls": row["successful_calls"],
            "success_rate": round(row["successful_calls"] / row["total_calls"] * 100, 2) if row["total_calls"] > 0 else 0
        }
        for row in cursor.fetchall()
    ]
    
    conn.close()
    
    return {
        "days": days,
        "performance_by_type": performance_by_type
    }

@app.get("/admin/satisfaction")
def get_user_satisfaction(days: int = 30):
    """Get user satisfaction analytics"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Calculate date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Get feedback statistics
    cursor.execute("""
        SELECT 
            AVG(rating) as avg_rating,
            COUNT(*) as total_feedback,
            SUM(CASE WHEN helpful = 1 THEN 1 ELSE 0 END) as helpful_count,
            SUM(CASE WHEN helpful = 0 THEN 1 ELSE 0 END) as unhelpful_count
        FROM user_feedback 
        WHERE created_at >= ?
    """, (start_date.isoformat(),))
    
    feedback_stats = cursor.fetchone()
    
    # Get feedback by type
    cursor.execute("""
        SELECT feedback_type, COUNT(*) as count
        FROM user_feedback 
        WHERE created_at >= ?
        GROUP BY feedback_type
    """, (start_date.isoformat(),))
    
    feedback_by_type = [{"type": row["feedback_type"], "count": row["count"]} for row in cursor.fetchall()]
    
    conn.close()
    
    return {
        "days": days,
        "average_rating": round(feedback_stats["avg_rating"], 2) if feedback_stats["avg_rating"] else 0,
        "total_feedback": feedback_stats["total_feedback"],
        "helpful_count": feedback_stats["helpful_count"] or 0,
        "unhelpful_count": feedback_stats["unhelpful_count"] or 0,
        "feedback_by_type": feedback_by_type
    }

@app.post("/feedback")
def submit_feedback(feedback: FeedbackRequest, user_id: int = 1):  # For demo purposes, using user_id=1
    """Submit user feedback"""
    track_user_feedback(
        user_id=user_id,
        feedback_type=feedback.feedback_type,
        rating=feedback.rating,
        comment=feedback.comment,
        helpful=feedback.helpful,
        question_id=feedback.question_id,
        document_id=feedback.document_id
    )
    
    return {"message": "Feedback submitted successfully"}

@app.get("/admin/users")
def get_users_admin(page: int = 1, per_page: int = 20):
    """Get all users (admin only)"""
    # In a real implementation, this would fetch users from the DB
    # For demo purposes:
    users = []
    for i in range(1, 11):  # Create 10 demo users
        users.append({
            "id": i,
            "email": f"user{i}@example.com",
            "full_name": f"User {i}",
            "is_active": True,
            "is_admin": i == 1,  # First user is admin
            "last_login": "2025-01-01T00:00:00",
            "created_at": "2025-01-01T00:00:00",
            "updated_at": "2025-01-01T00:00:00",
            "document_count": 5
        })

    return {
        "users": users[(page-1)*per_page:page*per_page],
        "total": len(users),
        "page": page,
        "per_page": per_page,
        "total_pages": (len(users) + per_page - 1) // per_page
    }

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "analytics-service"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import os
import psycopg2
from psycopg2.extras import RealDictCursor
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

# Internal API Key configuration
INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY")

async def verify_internal_api_key(x_internal_api_key: str = Header(None)):
    if not INTERNAL_API_KEY:
        return
    if x_internal_api_key != INTERNAL_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid Internal API Key")

# Initialize FastAPI app
app = FastAPI(
    title="Analytics Service", 
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
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@postgres:5432/app_db")

class FeedbackRequest(BaseModel):
    feedback_type: str
    rating: Optional[int] = None
    comment: Optional[str] = None
    helpful: Optional[bool] = None
    question_id: Optional[int] = None
    document_id: Optional[int] = None

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
            CREATE TABLE IF NOT EXISTS analytics_events (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                event_type TEXT NOT NULL,
                event_data TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS performance_metrics (
                id SERIAL PRIMARY KEY,
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
                id SERIAL PRIMARY KEY,
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
                id SERIAL PRIMARY KEY,
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
    except Exception as e:
        print(f"Error creating tables: {e}")

def track_analytics_event(user_id: int, event_type: str, event_data: Dict[str, Any]):
    """Track an analytics event"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO analytics_events (user_id, event_type, event_data)
        VALUES (%s, %s, %s)
    """, (user_id, event_type, json.dumps(event_data)))
    
    conn.commit()
    conn.close()

    # Process token usage if present
    if "token_usage" in event_data and event_data["token_usage"]:
        usages = event_data["token_usage"]
        if isinstance(usages, dict):
            usages = [usages]
            
        for usage in usages:
            track_token_usage(
                user_id=user_id,
                model_name=usage.get("model_name", "gpt-3.5-turbo"), # Default or extract from somewhere
                prompt_tokens=usage.get("prompt_tokens", 0),
                completion_tokens=usage.get("completion_tokens", 0),
                total_tokens=usage.get("total_tokens", 0)
            )

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
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
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
        VALUES (%s, %s, %s, %s, %s)
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
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (user_id, feedback_type, rating, comment, helpful, question_id, document_id))
    
    conn.commit()
    conn.close()

class AnalyticsEventRequest(BaseModel):
    user_id: int
    event_type: str
    event_data: Dict[str, Any]

@app.post("/events")
def receive_analytics_event(event: AnalyticsEventRequest):
    """Receive analytics event from other services"""
    print(f"DEBUG: Received event {event.event_type} from user {event.user_id}")
    
    if event.event_type == "performance_metric":
        try:
            track_performance_metric(
                user_id=event.user_id,
                metric_type=event.event_data.get("metric_type", "unknown"),
                start_time=datetime.fromisoformat(event.event_data["start_time"]),
                end_time=datetime.fromisoformat(event.event_data["end_time"]),
                success=event.event_data.get("success", False),
                error_message=event.event_data.get("error_message"),
                document_id=event.event_data.get("document_id"),
                question_id=event.event_data.get("question_id"),
                file_size_bytes=event.event_data.get("file_size_bytes")
            )
        except Exception as e:
            print(f"Error processing performance metric event: {e}")
            
    # Handle other event types...
    try:
        track_analytics_event(
            user_id=event.user_id,
            event_type=event.event_type,
            event_data=event.event_data
        )
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class PerformanceMetricRequest(BaseModel):
    user_id: int
    metric_type: str
    start_time: str
    end_time: str
    success: bool
    error_message: Optional[str] = None
    document_id: Optional[int] = None
    question_id: Optional[int] = None
    file_size_bytes: Optional[int] = None

@app.post("/metrics")
def receive_performance_metric(metric: PerformanceMetricRequest):
    """Receive performance metric from other services"""
    try:
        track_performance_metric(
            user_id=metric.user_id,
            metric_type=metric.metric_type,
            start_time=datetime.fromisoformat(metric.start_time),
            end_time=datetime.fromisoformat(metric.end_time),
            success=metric.success,
            error_message=metric.error_message,
            document_id=metric.document_id,
            question_id=metric.question_id,
            file_size_bytes=metric.file_size_bytes
        )
        return {"status": "success"}
    except Exception as e:
        print(f"Error tracking performance metric: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.on_event("startup")
def startup_event():
    """Initialize database tables on startup"""
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
        WHERE created_at >= %s
    """, (start_date.isoformat(),))
    total_events = cursor.fetchone()["total_events"]
    
    # Get total token usage
    cursor.execute("""
        SELECT SUM(total_tokens) as total_tokens FROM token_usage 
        WHERE created_at >= %s
    """, (start_date.isoformat(),))
    token_row = cursor.fetchone()
    total_tokens = token_row["total_tokens"] or 0
    
    # Get feedback stats
    cursor.execute("""
        SELECT 
            COUNT(*) as total_feedback,
            AVG(rating) as avg_rating,
            SUM(CASE WHEN helpful = TRUE THEN 1 ELSE 0 END) as helpful_count
        FROM user_feedback 
        WHERE created_at >= %s
    """, (start_date.isoformat(),))
    feedback_row = cursor.fetchone()
    total_feedback = feedback_row["total_feedback"]
    avg_rating = feedback_row["avg_rating"] or 0
    helpful_count = feedback_row["helpful_count"] or 0
    
    # Get performance stats
    # Postgres: EXTRACT(EPOCH FROM (end_time - start_time)) * 1000
    cursor.execute("""
        SELECT AVG(EXTRACT(EPOCH FROM (end_time - start_time)) * 1000) as avg_duration_ms
        FROM performance_metrics
        WHERE created_at >= %s
    """, (start_date.isoformat(),))
    perf_row = cursor.fetchone()
    avg_duration = perf_row["avg_duration_ms"] or 0
    
    # Get user stats
    cursor.execute("""
        SELECT COUNT(DISTINCT user_id) as active_users
        FROM analytics_events
        WHERE created_at >= %s
    """, (start_date.isoformat(),))
    active_users = cursor.fetchone()["active_users"]

    # Get document stats
    cursor.execute("""
        SELECT COUNT(*) as uploaded_docs
        FROM analytics_events
        WHERE event_type = 'document_uploaded' AND created_at >= %s
    """, (start_date.isoformat(),))
    uploaded_docs = cursor.fetchone()["uploaded_docs"]

    # Get total documents (all time)
    cursor.execute("SELECT COUNT(*) as total_docs FROM analytics_events WHERE event_type = 'document_uploaded'")
    total_docs = cursor.fetchone()["total_docs"]

    conn.close()
    
    # Construct response matching frontend interface
    return {
        "period_days": days,
        "users": {
            "total": active_users, # Approximation based on active users
            "active_in_period": active_users,
            "activity_rate": 100.0 if active_users > 0 else 0
        },
        "documents": {
            "total": total_docs,
            "uploaded_in_period": uploaded_docs
        },
        "questions": {
            "total": total_events, # Approximation
            "asked_in_period": total_events
        },
        "tokens": {
            "total_tokens": total_tokens,
            "input_tokens": int(total_tokens * 0.7), # Approximation
            "output_tokens": int(total_tokens * 0.3), # Approximation
            "estimated_cost": total_tokens * 0.000002 # Approximation ($0.002 per 1k tokens)
        },
        "performance": {
            "avg_analysis_time_seconds": avg_duration,
            "avg_question_time_seconds": avg_duration # Using same metric for now
        },
        "feedback": {
            "average_rating": round(avg_rating, 1),
            "total_feedback": total_feedback,
            "helpful_responses": helpful_count,
            "unhelpful_responses": total_feedback - helpful_count,
            "satisfaction_rate": (helpful_count / total_feedback * 100) if total_feedback > 0 else 0
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
        WHERE created_at >= %s 
        GROUP BY event_type
    """, (start_date.isoformat(),))
    
    operation_stats = [{"operation": row["event_type"], "count": row["count"]} for row in cursor.fetchall()]
    
    # Get daily usage
    cursor.execute("""
        SELECT date(created_at) as day, COUNT(*) as count
        FROM analytics_events
        WHERE created_at >= %s
        GROUP BY date(created_at)
        ORDER BY day
    """, (start_date.isoformat(),))
    
    daily_usage = [{"date": row["day"], "events": row["count"]} for row in cursor.fetchall()]
    
    conn.close()
    
    return {
        "hourly_usage": [{"hour": i, "events": 0} for i in range(24)], # Keep mock for hourly for now
        "daily_usage": daily_usage,
        "top_users": [],
        "operation_stats": operation_stats
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
        SELECT model_name, SUM(total_tokens) as total_tokens
        FROM token_usage 
        WHERE created_at >= %s 
        GROUP BY model_name
    """, (start_date.isoformat(),))
    
    vendor_usage = [
        {
            "vendor": row["model_name"], 
            "total_tokens": row["total_tokens"],
            "total_cost": row["total_tokens"] * 0.000002,
            "operation_count": 0
        }
        for row in cursor.fetchall()
    ]
    
    # Get daily token trend
    cursor.execute("""
        SELECT date(created_at) as day, SUM(total_tokens) as tokens
        FROM token_usage
        WHERE created_at >= %s
        GROUP BY date(created_at)
        ORDER BY day
    """, (start_date.isoformat(),))
    
    daily_trend = [
        {"date": row["day"], "tokens": row["tokens"]}
        for row in cursor.fetchall()
    ]
    
    conn.close()
    
    return {
        "vendor_usage": vendor_usage,
        "operation_usage": [],
        "daily_trend": daily_trend,
        "top_users": []
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
               AVG(EXTRACT(EPOCH FROM (end_time - start_time)) * 1000) as avg_duration_ms,
               COUNT(*) as total_calls,
               SUM(CASE WHEN success = TRUE THEN 1 ELSE 0 END) as successful_calls
        FROM performance_metrics 
        WHERE created_at >= %s 
        GROUP BY metric_type
    """, (start_date.isoformat(),))
    
    operation_performance = [
        {
            "operation": row["metric_type"],
            "avg_duration": round(row["avg_duration_ms"], 2),
            "min_duration": 0, # Not tracking min/max yet
            "max_duration": 0,
            "operation_count": row["total_calls"],
            "success_rate": round(row["successful_calls"] / row["total_calls"] * 100, 2) if row["total_calls"] > 0 else 0
        }
        for row in cursor.fetchall()
    ]
    
    # Get daily performance
    cursor.execute("""
        SELECT date(created_at) as day, 
               AVG(EXTRACT(EPOCH FROM (end_time - start_time)) * 1000) as avg_duration,
               COUNT(*) as count
        FROM performance_metrics
        WHERE created_at >= %s
        GROUP BY date(created_at)
        ORDER BY day
    """, (start_date.isoformat(),))
    
    daily_performance = [
        {
            "date": row["day"], 
            "avg_duration": row["avg_duration"], 
            "operation_count": row["count"]
        } 
        for row in cursor.fetchall()
    ]

    # Get file size vs processing time correlation
    # Postgres: event_data::json->>'file_size'
    cursor.execute("""
        SELECT 
            ae.event_data::json->>'file_size' as file_size,
            EXTRACT(EPOCH FROM (pm.end_time - pm.start_time)) * 1000 as duration_ms
        FROM performance_metrics pm
        JOIN analytics_events ae ON pm.document_id = (ae.event_data::json->>'document_id')::int
        WHERE pm.metric_type = 'document_processing'
        AND ae.event_type = 'document_analyzed'
        AND pm.created_at >= %s
        AND pm.success = TRUE
    """, (start_date.isoformat(),))
    
    file_size_correlation = [
        {
            "file_size_mb": round(float(row["file_size"]) / (1024 * 1024), 2) if row["file_size"] else 0,
            "duration_seconds": round(row["duration_ms"], 2) # Frontend expects duration_seconds but label says ms, keeping raw ms value
        }
        for row in cursor.fetchall()
        if row["file_size"] is not None
    ]

    conn.close()
    
    return {
        "operation_performance": operation_performance,
        "daily_performance": daily_performance,
        "file_size_correlation": file_size_correlation,
        "error_rates": []
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
            SUM(CASE WHEN helpful = TRUE THEN 1 ELSE 0 END) as helpful_count,
            SUM(CASE WHEN helpful = FALSE THEN 1 ELSE 0 END) as unhelpful_count
        FROM user_feedback 
        WHERE created_at >= %s
    """, (start_date.isoformat(),))
    
    feedback_stats = cursor.fetchone()
    total_feedback = feedback_stats["total_feedback"]
    helpful_count = feedback_stats["helpful_count"] or 0
    unhelpful_count = feedback_stats["unhelpful_count"] or 0
    
    # Get feedback by type
    cursor.execute("""
        SELECT feedback_type, AVG(rating) as avg_rating, COUNT(*) as count
        FROM user_feedback 
        WHERE created_at >= %s
        GROUP BY feedback_type
    """, (start_date.isoformat(),))
    
    feedback_by_type = [
        {
            "type": row["feedback_type"], 
            "avg_rating": row["avg_rating"] or 0, 
            "count": row["count"]
        } 
        for row in cursor.fetchall()
    ]
    
    conn.close()
    
    return {
        "overall_satisfaction": {
            "average_rating": round(feedback_stats["avg_rating"], 2) if feedback_stats["avg_rating"] else 0,
            "total_feedback": total_feedback,
            "positive_rate": (helpful_count / total_feedback * 100) if total_feedback > 0 else 0,
            "negative_rate": (unhelpful_count / total_feedback * 100) if total_feedback > 0 else 0,
            "helpful_rate": (helpful_count / total_feedback * 100) if total_feedback > 0 else 0
        },
        "feedback_by_type": feedback_by_type,
        "daily_satisfaction": [],
        "recent_comments": []
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
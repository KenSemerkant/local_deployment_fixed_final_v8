from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from enum import Enum
import os
import logging

# Initialize FastAPI app
app = FastAPI(
    title="Analytics Service",
    version="1.0.0",
    root_path="/analytics"
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

# Database models
Base = declarative_base()

class EventCategory(str, Enum):
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    DOCUMENT_UPLOAD = "DOCUMENT_UPLOAD"
    DOCUMENT_VIEW = "DOCUMENT_VIEW"
    ANALYSIS_START = "ANALYSIS_START"
    ANALYSIS_COMPLETE = "ANALYSIS_COMPLETE"
    QUESTION_ASK = "QUESTION_ASK"
    QUESTION_VIEW = "QUESTION_VIEW"
    FEEDBACK_SUBMIT = "FEEDBACK_SUBMIT"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    full_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    last_login = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class AnalyticsEvent(Base):
    __tablename__ = "analytics_events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    event_type = Column(String)  # LOGIN, DOCUMENT_UPLOAD, ANALYSIS_START, etc.
    event_data = Column(Text)  # JSON string with event-specific data
    timestamp = Column(DateTime, default=datetime.utcnow)
    session_id = Column(String, nullable=True)  # Browser session ID
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)

    user = relationship("User")

class TokenUsage(Base):
    __tablename__ = "token_usage"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    document_id = Column(Integer, nullable=True)
    question_id = Column(Integer, nullable=True)
    operation_type = Column(String)  # ANALYSIS, QUESTION, EMBEDDING, SUMMARY
    model_name = Column(String)
    vendor = Column(String)
    input_tokens = Column(Integer, default=0)
    output_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    cost_estimate = Column(Float, default=0.0)  # Estimated cost in USD
    timestamp = Column(DateTime, default=datetime.utcnow)

class PerformanceMetrics(Base):
    __tablename__ = "performance_metrics"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    document_id = Column(Integer, nullable=True)
    question_id = Column(Integer, nullable=True)
    operation_type = Column(String)  # DOCUMENT_ANALYSIS, EMBEDDING_CREATION, QUESTION_ANSWERING
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    duration_seconds = Column(Float)
    file_size_bytes = Column(Integer, nullable=True)
    success = Column(Boolean, default=True)
    error_message = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

class UserFeedback(Base):
    __tablename__ = "user_feedback"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    question_id = Column(Integer, nullable=True)
    document_id = Column(Integer, nullable=True)
    feedback_type = Column(String)  # RATING, COMMENT, THUMBS_UP, THUMBS_DOWN
    rating = Column(Integer, nullable=True)  # 1-5 scale
    comment = Column(Text, nullable=True)
    helpful = Column(Boolean, nullable=True)  # True for thumbs up, False for thumbs down
    timestamp = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")

# Pydantic models
class AnalyticsOverviewResponse(BaseModel):
    period_days: int
    users: Dict[str, Any]
    documents: Dict[str, Any]
    questions: Dict[str, Any]
    tokens: Dict[str, Any]
    performance: Dict[str, Any]
    feedback: Dict[str, Any]
    error: Optional[str] = None

class UsagePatternsResponse(BaseModel):
    hourly_usage: List[Dict[str, Any]]
    daily_usage: List[Dict[str, Any]]
    top_users: List[Dict[str, Any]]
    operation_stats: List[Dict[str, Any]]
    error: Optional[str] = None

class TokenAnalyticsResponse(BaseModel):
    vendor_usage: List[Dict[str, Any]]
    operation_usage: List[Dict[str, Any]]
    daily_trend: List[Dict[str, Any]]
    top_users: List[Dict[str, Any]]
    error: Optional[str] = None

class PerformanceAnalyticsResponse(BaseModel):
    operation_performance: List[Dict[str, Any]]
    daily_performance: List[Dict[str, Any]]
    file_size_correlation: List[Dict[str, Any]]
    error_rates: List[Dict[str, Any]]
    error: Optional[str] = None

class UserSatisfactionResponse(BaseModel):
    overall_satisfaction: Dict[str, Any]
    feedback_by_type: List[Dict[str, Any]]
    daily_satisfaction: List[Dict[str, Any]]
    recent_comments: List[Dict[str, Any]]
    error: Optional[str] = None

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test_analytics.db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Mock data generators for demonstration
def generate_mock_overview_data(period_days: int = 30) -> AnalyticsOverviewResponse:
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=period_days)

    return AnalyticsOverviewResponse(
        period_days=period_days,
        users={
            "total": 125,
            "active_in_period": 75,
            "activity_rate": 60.0
        },
        documents={
            "total": 250,
            "uploaded_in_period": 85
        },
        questions={
            "total": 1250,
            "asked_in_period": 750
        },
        tokens={
            "total_tokens": 4500000,
            "input_tokens": 3000000,
            "output_tokens": 1500000,
            "estimated_cost": 22.50
        },
        performance={
            "avg_analysis_time_seconds": 45.2,
            "avg_question_time_seconds": 12.7
        },
        feedback={
            "average_rating": 4.2,
            "total_feedback": 450,
            "helpful_responses": 380,
            "unhelpful_responses": 70,
            "satisfaction_rate": 84.4
        }
    )

def generate_mock_usage_data(period_days: int = 30) -> UsagePatternsResponse:
    return UsagePatternsResponse(
        hourly_usage=[
            {"hour": 8, "events": 45},
            {"hour": 9, "events": 67},
            {"hour": 10, "events": 89},
            {"hour": 11, "events": 78},
            {"hour": 12, "events": 54},
            {"hour": 13, "events": 62},
            {"hour": 14, "events": 81},
            {"hour": 15, "events": 75},
            {"hour": 16, "events": 68},
        ],
        daily_usage=[
            {"date": "2025-11-15", "events": 125},
            {"date": "2025-11-16", "events": 132},
            {"date": "2025-11-17", "events": 145},
            {"date": "2025-11-18", "events": 128},
            {"date": "2025-11-19", "events": 143},
            {"date": "2025-11-20", "events": 150},
            {"date": "2025-11-21", "events": 138},
        ],
        top_users=[
            {"email": "john@example.com", "name": "John Doe", "activity_count": 42},
            {"email": "sarah@example.com", "name": "Sarah Smith", "activity_count": 38},
            {"email": "mike@example.com", "name": "Mike Johnson", "activity_count": 35},
        ],
        operation_stats=[
            {"operation": "LOGIN", "count": 2500},
            {"operation": "DOCUMENT_UPLOAD", "count": 85},
            {"operation": "ANALYSIS_START", "count": 75},
            {"operation": "QUESTION_ASK", "count": 750},
        ]
    )

@app.get("/")
def read_root():
    return {"service": "analytics-service", "status": "running"}

@app.get("/overview", response_model=AnalyticsOverviewResponse)
def get_analytics_overview(days: int = 30):
    return generate_mock_overview_data(days)

@app.get("/usage-patterns", response_model=UsagePatternsResponse)
def get_usage_patterns(days: int = 30):
    return generate_mock_usage_data(days)

@app.get("/tokens", response_model=TokenAnalyticsResponse)
def get_token_analytics(days: int = 30):
    return TokenAnalyticsResponse(
        vendor_usage=[
            {"vendor": "openai", "total_tokens": 2500000, "total_cost": 12.50, "operation_count": 450},
            {"vendor": "ollama", "total_tokens": 1500000, "total_cost": 0.0, "operation_count": 300},
            {"vendor": "lmstudio", "total_tokens": 500000, "total_cost": 0.0, "operation_count": 100}
        ],
        operation_usage=[
            {"operation": "ANALYSIS", "total_tokens": 3000000, "avg_tokens": 4000, "total_cost": 15.0},
            {"operation": "QUESTION", "total_tokens": 1000000, "avg_tokens": 1333, "total_cost": 5.0},
            {"operation": "EMBEDDING", "total_tokens": 500000, "avg_tokens": 500, "total_cost": 2.5}
        ],
        daily_trend=[
            {"date": "2025-11-15", "tokens": 150000, "cost": 0.75},
            {"date": "2025-11-16", "tokens": 165000, "cost": 0.83},
            {"date": "2025-11-17", "tokens": 178000, "cost": 0.89},
            {"date": "2025-11-18", "tokens": 162000, "cost": 0.81},
            {"date": "2025-11-19", "tokens": 175000, "cost": 0.88},
            {"date": "2025-11-20", "tokens": 180000, "cost": 0.90},
            {"date": "2025-11-21", "tokens": 170000, "cost": 0.85},
        ],
        top_users=[
            {"email": "john@example.com", "name": "John Doe", "total_tokens": 150000, "total_cost": 0.75},
            {"email": "sarah@example.com", "name": "Sarah Smith", "total_tokens": 125000, "total_cost": 0.63},
            {"email": "mike@example.com", "name": "Mike Johnson", "total_tokens": 100000, "total_cost": 0.50},
        ]
    )

@app.get("/performance", response_model=PerformanceAnalyticsResponse)
def get_performance_analytics(days: int = 30):
    return PerformanceAnalyticsResponse(
        operation_performance=[
            {
                "operation": "DOCUMENT_ANALYSIS",
                "avg_duration": 45.2,
                "min_duration": 12.3,
                "max_duration": 120.5,
                "operation_count": 75,
                "success_rate": 96.0
            },
            {
                "operation": "EMBEDDING_CREATION",
                "avg_duration": 18.7,
                "min_duration": 5.2,
                "max_duration": 45.8,
                "operation_count": 85,
                "success_rate": 98.8
            },
            {
                "operation": "QUESTION_ANSWERING",
                "avg_duration": 12.7,
                "min_duration": 2.1,
                "max_duration": 35.4,
                "operation_count": 750,
                "success_rate": 97.3
            }
        ],
        daily_performance=[
            {"date": "2025-11-15", "avg_duration": 42.5, "operation_count": 12},
            {"date": "2025-11-16", "avg_duration": 44.3, "operation_count": 15},
            {"date": "2025-11-17", "avg_duration": 45.8, "operation_count": 18},
            {"date": "2025-11-18", "avg_duration": 46.1, "operation_count": 14},
            {"date": "2025-11-19", "avg_duration": 43.9, "operation_count": 16},
            {"date": "2025-11-20", "avg_duration": 45.2, "operation_count": 18},
            {"date": "2025-11-21", "avg_duration": 44.7, "operation_count": 12},
        ],
        file_size_correlation=[
            {"file_size_mb": 2.5, "duration_seconds": 35.2},
            {"file_size_mb": 5.1, "duration_seconds": 52.7},
            {"file_size_mb": 7.8, "duration_seconds": 68.4},
            {"file_size_mb": 12.3, "duration_seconds": 89.1},
            {"file_size_mb": 18.7, "duration_seconds": 122.5},
        ],
        error_rates=[
            {"operation": "DOCUMENT_ANALYSIS", "total_operations": 75, "error_count": 3, "error_rate": 4.0},
            {"operation": "EMBEDDING_CREATION", "total_operations": 85, "error_count": 1, "error_rate": 1.2},
            {"operation": "QUESTION_ANSWERING", "total_operations": 750, "error_count": 20, "error_rate": 2.7},
        ]
    )

@app.get("/satisfaction", response_model=UserSatisfactionResponse)
def get_user_satisfaction(days: int = 30):
    return UserSatisfactionResponse(
        overall_satisfaction={
            "average_rating": 4.2,
            "total_feedback": 450,
            "positive_rate": 78.7,
            "negative_rate": 15.6,
            "helpful_rate": 84.4
        },
        feedback_by_type=[
            {"type": "RATING", "avg_rating": 4.2, "count": 350},
            {"type": "THUMBS_UP", "avg_rating": 4.8, "count": 240},
            {"type": "THUMBS_DOWN", "avg_rating": 2.1, "count": 110},
            {"type": "COMMENT", "avg_rating": 3.9, "count": 100},
        ],
        daily_satisfaction=[
            {"date": "2025-11-15", "avg_rating": 4.1, "feedback_count": 18},
            {"date": "2025-11-16", "avg_rating": 4.3, "feedback_count": 22},
            {"date": "2025-11-17", "avg_rating": 4.2, "feedback_count": 19},
            {"date": "2025-11-18", "avg_rating": 4.0, "feedback_count": 21},
            {"date": "2025-11-19", "avg_rating": 4.4, "feedback_count": 24},
            {"date": "2025-11-20", "avg_rating": 4.3, "feedback_count": 20},
            {"date": "2025-11-21", "avg_rating": 4.1, "feedback_count": 16},
        ],
        recent_comments=[
            {"comment": "Very helpful analysis, exactly what I needed!", "rating": 5, "timestamp": "2025-11-21T10:30:00", "user_email": "john@example.com"},
            {"comment": "The response was accurate and well-structured.", "rating": 5, "timestamp": "2025-11-21T09:15:00", "user_email": "sarah@example.com"},
            {"comment": "Could be more detailed in the financial projections section.", "rating": 3, "timestamp": "2025-11-21T08:45:00", "user_email": "mike@example.com"},
            {"comment": "Great insights into the risk factors.", "rating": 5, "timestamp": "2025-11-20T16:20:00", "user_email": "lisa@example.com"},
            {"comment": "The analysis helped me understand the cash flow better.", "rating": 4, "timestamp": "2025-11-20T14:30:00", "user_email": "david@example.com"},
        ]
    )

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "analytics-service"}
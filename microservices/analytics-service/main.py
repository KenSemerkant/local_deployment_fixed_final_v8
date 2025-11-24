from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import json
import random
from datetime import datetime, timedelta

# Pydantic models
class AnalyticsOverviewResponse(BaseModel):
    period_days: int
    users: Dict[str, Any]
    documents: Dict[str, Any]
    questions: Dict[str, Any]
    tokens: Dict[str, Any]
    performance: Dict[str, Any]
    feedback: Dict[str, Any]

class UsagePatternsResponse(BaseModel):
    hourly_usage: List[Dict[str, Any]]
    daily_usage: List[Dict[str, Any]]
    top_users: List[Dict[str, Any]]
    operation_stats: List[Dict[str, Any]]

class TokenAnalyticsResponse(BaseModel):
    vendor_usage: List[Dict[str, Any]]
    operation_usage: List[Dict[str, Any]]
    daily_trend: List[Dict[str, Any]]
    top_users: List[Dict[str, Any]]

class PerformanceAnalyticsResponse(BaseModel):
    operation_performance: List[Dict[str, Any]]
    daily_performance: List[Dict[str, Any]]
    file_size_correlation: List[Dict[str, Any]]
    error_rates: List[Dict[str, Any]]

class UserSatisfactionResponse(BaseModel):
    overall_satisfaction: Dict[str, Any]
    feedback_by_type: List[Dict[str, Any]]
    daily_satisfaction: List[Dict[str, Any]]
    recent_comments: List[Dict[str, Any]]

# Initialize FastAPI app
app = FastAPI(
    title="Analytics Service",
    version="1.0.0",
    root_path="/analytics"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"service": "analytics-service", "status": "running"}

@app.get("/dashboard", response_model=AnalyticsOverviewResponse)
def get_analytics_dashboard(days: int = 30):
    # In a real implementation, this would fetch from database
    # For now, return mock analytics data
    return AnalyticsOverviewResponse(
        period_days=days,
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

@app.get("/usage-patterns", response_model=UsagePatternsResponse)
def get_usage_patterns(days: int = 30):
    # Mock usage patterns data
    hourly_usage = []
    for hour in range(24):
        hourly_usage.append({
            "hour": hour,
            "events": random.randint(10, 100)
        })
    
    daily_usage = []
    for day in range(days):
        date = (datetime.now() - timedelta(days=day)).strftime("%Y-%m-%d")
        daily_usage.append({
            "date": date,
            "events": random.randint(20, 200)
        })
    
    return UsagePatternsResponse(
        hourly_usage=hourly_usage,
        daily_usage=daily_usage,
        top_users=[
            {"email": "john@example.com", "name": "John Doe", "activity_count": 142},
            {"email": "sarah@example.com", "name": "Sarah Smith", "activity_count": 98},
            {"email": "mike@example.com", "name": "Mike Johnson", "activity_count": 87}
        ],
        operation_stats=[
            {"operation": "DOCUMENT_UPLOAD", "count": 125},
            {"operation": "DOCUMENT_ANALYSIS", "count": 98},
            {"operation": "QUESTION_ASKING", "count": 342},
            {"operation": "EXPORT", "count": 89}
        ]
    )

@app.get("/tokens", response_model=TokenAnalyticsResponse)
def get_token_analytics(days: int = 30):
    # Mock token analytics
    return TokenAnalyticsResponse(
        vendor_usage=[
            {"vendor": "openai", "total_tokens": 2500000, "total_cost": 12.50},
            {"vendor": "ollama", "total_tokens": 1500000, "total_cost": 0.0},
            {"vendor": "lmstudio", "total_tokens": 500000, "total_cost": 0.0}
        ],
        operation_usage=[
            {"operation": "ANALYSIS", "total_tokens": 3000000, "avg_tokens": 4000, "total_cost": 15.00},
            {"operation": "QUESTION", "total_tokens": 1000000, "avg_tokens": 1333, "total_cost": 5.00},
            {"operation": "EMBEDDING", "total_tokens": 500000, "avg_tokens": 500, "total_cost": 2.50}
        ],
        daily_trend=[
            {"date": (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d"), "tokens": random.randint(100000, 200000), "cost": round(random.uniform(5.0, 10.0), 2)}
            for i in range(days)
        ],
        top_users=[
            {"email": "john@example.com", "name": "John Doe", "total_tokens": 150000, "total_cost": 0.75},
            {"email": "sarah@example.com", "name": "Sarah Smith", "total_tokens": 125000, "total_cost": 0.63},
            {"email": "mike@example.com", "name": "Mike Johnson", "total_tokens": 100000, "total_cost": 0.50}
        ]
    )

@app.get("/performance", response_model=PerformanceAnalyticsResponse)
def get_performance_analytics(days: int = 30):
    # Mock performance analytics
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
            {
                "date": (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d"),
                "avg_duration": round(random.uniform(10.0, 50.0), 2),
                "operation_count": random.randint(20, 50)
            }
            for i in range(days)
        ],
        file_size_correlation=[
            {"file_size_mb": 2.5, "duration_seconds": 35.2},
            {"file_size_mb": 5.1, "duration_seconds": 52.7},
            {"file_size_mb": 7.8, "duration_seconds": 68.4},
            {"file_size_mb": 12.3, "duration_seconds": 89.1},
            {"file_size_mb": 18.7, "duration_seconds": 122.5}
        ],
        error_rates=[
            {"operation": "DOCUMENT_ANALYSIS", "total_operations": 75, "error_count": 3, "error_rate": 4.0},
            {"operation": "EMBEDDING_CREATION", "total_operations": 85, "error_count": 1, "error_rate": 1.2},
            {"operation": "QUESTION_ANSWERING", "total_operations": 750, "error_count": 20, "error_rate": 2.7}
        ]
    )

@app.get("/satisfaction", response_model=UserSatisfactionResponse)
def get_user_satisfaction(days: int = 30):
    # Mock user satisfaction metrics
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
            {"type": "COMMENT", "avg_rating": 3.9, "count": 100}
        ],
        daily_satisfaction=[
            {
                "date": (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d"),
                "avg_rating": round(random.uniform(3.8, 4.6), 2),
                "feedback_count": random.randint(10, 25)
            }
            for i in range(days)
        ],
        recent_comments=[
            {"comment": "Very helpful analysis, exactly what I needed!", "rating": 5, "timestamp": "2025-11-22T10:30:00Z", "user_email": "john@example.com"},
            {"comment": "The response was accurate and well-structured.", "rating": 5, "timestamp": "2025-11-22T09:15:00Z", "user_email": "sarah@example.com"},
            {"comment": "Could be more detailed in the financial projections section.", "rating": 3, "timestamp": "2025-11-21T16:20:00Z", "user_email": "mike@example.com"},
            {"comment": "Great insights into the risk factors.", "rating": 5, "timestamp": "2025-11-21T14:30:00Z", "user_email": "lisa@example.com"},
            {"comment": "The analysis helped me understand the cash flow better.", "rating": 4, "timestamp": "2025-11-21T12:45:00Z", "user_email": "david@example.com"}
        ]
    )

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "analytics-service"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)
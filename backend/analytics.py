"""
Analytics Module for AI Financial Analyst Application
Provides comprehensive analytics tracking and reporting capabilities.
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc, asc
from collections import defaultdict

from models import (
    User, Document, Question, AnalyticsEvent, TokenUsage, 
    PerformanceMetrics, UserFeedback, AnalysisResult, QASession
)

logger = logging.getLogger(__name__)

# Token cost estimates (USD per 1K tokens) - approximate values
TOKEN_COSTS = {
    "openai": {
        "gpt-4o": {"input": 0.005, "output": 0.015},
        "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
        "gpt-4-turbo": {"input": 0.01, "output": 0.03},
        "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015}
    },
    "anthropic": {
        "claude-3-opus": {"input": 0.015, "output": 0.075},
        "claude-3-sonnet": {"input": 0.003, "output": 0.015},
        "claude-3-haiku": {"input": 0.00025, "output": 0.00125}
    },
    "ollama": {"default": {"input": 0.0, "output": 0.0}},  # Local models are free
    "lmstudio": {"default": {"input": 0.0, "output": 0.0}},  # Local models are free
    "meta": {"default": {"input": 0.0, "output": 0.0}}  # Local models are free
}

def track_analytics_event(
    db: Session,
    user_id: int,
    event_type: str,
    event_data: Dict[str, Any] = None,
    session_id: str = None,
    ip_address: str = None,
    user_agent: str = None
):
    """Track an analytics event."""
    try:
        event = AnalyticsEvent(
            user_id=user_id,
            event_type=event_type,
            event_data=json.dumps(event_data or {}),
            session_id=session_id,
            ip_address=ip_address,
            user_agent=user_agent
        )
        db.add(event)
        db.commit()
        logger.info(f"Tracked analytics event: {event_type} for user {user_id}")
    except Exception as e:
        logger.error(f"Error tracking analytics event: {e}")
        db.rollback()

def track_token_usage(
    db: Session,
    user_id: int,
    operation_type: str,
    model_name: str,
    vendor: str,
    input_tokens: int = 0,
    output_tokens: int = 0,
    document_id: int = None,
    question_id: int = None
):
    """Track token usage for LLM operations."""
    try:
        total_tokens = input_tokens + output_tokens
        
        # Calculate cost estimate
        cost_estimate = calculate_token_cost(vendor, model_name, input_tokens, output_tokens)
        
        token_usage = TokenUsage(
            user_id=user_id,
            document_id=document_id,
            question_id=question_id,
            operation_type=operation_type,
            model_name=model_name,
            vendor=vendor,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            cost_estimate=cost_estimate
        )
        db.add(token_usage)
        db.commit()
        logger.info(f"Tracked token usage: {total_tokens} tokens for user {user_id}")
    except Exception as e:
        logger.error(f"Error tracking token usage: {e}")
        db.rollback()

def track_performance_metric(
    db: Session,
    user_id: int,
    operation_type: str,
    start_time: datetime,
    end_time: datetime,
    success: bool = True,
    error_message: str = None,
    document_id: int = None,
    question_id: int = None,
    file_size_bytes: int = None
):
    """Track performance metrics for operations."""
    try:
        duration_seconds = (end_time - start_time).total_seconds()
        
        metric = PerformanceMetrics(
            user_id=user_id,
            document_id=document_id,
            question_id=question_id,
            operation_type=operation_type,
            start_time=start_time,
            end_time=end_time,
            duration_seconds=duration_seconds,
            file_size_bytes=file_size_bytes,
            success=success,
            error_message=error_message
        )
        db.add(metric)
        db.commit()
        logger.info(f"Tracked performance metric: {operation_type} took {duration_seconds:.2f}s")
    except Exception as e:
        logger.error(f"Error tracking performance metric: {e}")
        db.rollback()

def track_user_feedback(
    db: Session,
    user_id: int,
    feedback_type: str,
    rating: Optional[int] = None,
    comment: Optional[str] = None,
    helpful: Optional[bool] = None,
    question_id: Optional[int] = None,
    document_id: Optional[int] = None
):
    """Track user feedback."""
    try:
        feedback = UserFeedback(
            user_id=user_id,
            question_id=question_id,
            document_id=document_id,
            feedback_type=feedback_type,
            rating=rating,
            comment=comment,
            helpful=helpful
        )
        db.add(feedback)
        db.commit()
        logger.info(f"Tracked user feedback: {feedback_type} from user {user_id}")
    except Exception as e:
        logger.error(f"Error tracking user feedback: {e}")
        db.rollback()

def calculate_token_cost(vendor: str, model_name: str, input_tokens: int, output_tokens: int) -> float:
    """Calculate estimated cost for token usage."""
    try:
        vendor_costs = TOKEN_COSTS.get(vendor.lower(), {})
        model_costs = vendor_costs.get(model_name.lower(), vendor_costs.get("default", {"input": 0.0, "output": 0.0}))
        
        input_cost = (input_tokens / 1000) * model_costs.get("input", 0.0)
        output_cost = (output_tokens / 1000) * model_costs.get("output", 0.0)
        
        return input_cost + output_cost
    except Exception as e:
        logger.error(f"Error calculating token cost: {e}")
        return 0.0

def get_analytics_overview(db: Session, days: int = 30) -> Dict[str, Any]:
    """Get comprehensive analytics overview."""
    try:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Basic user statistics
        total_users = db.query(User).count()
        active_users = db.query(User).filter(User.last_login >= start_date).count()
        
        # Document statistics
        total_documents = db.query(Document).count()
        documents_period = db.query(Document).filter(Document.created_at >= start_date).count()
        
        # Question statistics
        total_questions = db.query(Question).count()
        questions_period = db.query(Question).filter(Question.created_at >= start_date).count()
        
        # Token usage statistics
        token_stats = db.query(
            func.sum(TokenUsage.total_tokens).label('total_tokens'),
            func.sum(TokenUsage.input_tokens).label('input_tokens'),
            func.sum(TokenUsage.output_tokens).label('output_tokens'),
            func.sum(TokenUsage.cost_estimate).label('total_cost')
        ).filter(TokenUsage.timestamp >= start_date).first()
        
        # Performance statistics
        avg_analysis_time = db.query(func.avg(PerformanceMetrics.duration_seconds)).filter(
            and_(
                PerformanceMetrics.operation_type == 'DOCUMENT_ANALYSIS',
                PerformanceMetrics.timestamp >= start_date,
                PerformanceMetrics.success == True
            )
        ).scalar() or 0
        
        avg_question_time = db.query(func.avg(PerformanceMetrics.duration_seconds)).filter(
            and_(
                PerformanceMetrics.operation_type == 'QUESTION_ANSWERING',
                PerformanceMetrics.timestamp >= start_date,
                PerformanceMetrics.success == True
            )
        ).scalar() or 0
        
        # User feedback statistics - simplified approach
        feedback_stats = db.query(
            func.avg(UserFeedback.rating).label('avg_rating'),
            func.count(UserFeedback.id).label('total_feedback')
        ).filter(UserFeedback.timestamp >= start_date).first()

        # Get helpful/unhelpful counts separately
        helpful_count = db.query(func.count(UserFeedback.id)).filter(
            and_(UserFeedback.timestamp >= start_date, UserFeedback.helpful == True)
        ).scalar() or 0

        unhelpful_count = db.query(func.count(UserFeedback.id)).filter(
            and_(UserFeedback.timestamp >= start_date, UserFeedback.helpful == False)
        ).scalar() or 0
        
        return {
            "period_days": days,
            "users": {
                "total": total_users,
                "active_in_period": active_users,
                "activity_rate": (active_users / total_users * 100) if total_users > 0 else 0
            },
            "documents": {
                "total": total_documents,
                "uploaded_in_period": documents_period
            },
            "questions": {
                "total": total_questions,
                "asked_in_period": questions_period
            },
            "tokens": {
                "total_tokens": token_stats.total_tokens or 0,
                "input_tokens": token_stats.input_tokens or 0,
                "output_tokens": token_stats.output_tokens or 0,
                "estimated_cost": round(token_stats.total_cost or 0, 4)
            },
            "performance": {
                "avg_analysis_time_seconds": round(avg_analysis_time, 2),
                "avg_question_time_seconds": round(avg_question_time, 2)
            },
            "feedback": {
                "average_rating": round(feedback_stats.avg_rating or 0, 2),
                "total_feedback": feedback_stats.total_feedback or 0,
                "helpful_responses": helpful_count,
                "unhelpful_responses": unhelpful_count,
                "satisfaction_rate": (
                    helpful_count / max(helpful_count + unhelpful_count, 1) * 100
                )
            }
        }
    except Exception as e:
        logger.error(f"Error getting analytics overview: {e}")
        return {"error": str(e)}

def get_usage_patterns(db: Session, days: int = 30) -> Dict[str, Any]:
    """Get usage patterns and trends."""
    try:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Hourly usage pattern
        hourly_usage = db.query(
            func.extract('hour', AnalyticsEvent.timestamp).label('hour'),
            func.count(AnalyticsEvent.id).label('event_count')
        ).filter(
            and_(
                AnalyticsEvent.timestamp >= start_date,
                AnalyticsEvent.event_type.in_(['LOGIN', 'DOCUMENT_UPLOAD', 'QUESTION_ASK'])
            )
        ).group_by(func.extract('hour', AnalyticsEvent.timestamp)).all()
        
        # Daily usage pattern
        daily_usage = db.query(
            func.date(AnalyticsEvent.timestamp).label('date'),
            func.count(AnalyticsEvent.id).label('event_count')
        ).filter(
            and_(
                AnalyticsEvent.timestamp >= start_date,
                AnalyticsEvent.event_type.in_(['LOGIN', 'DOCUMENT_UPLOAD', 'QUESTION_ASK'])
            )
        ).group_by(func.date(AnalyticsEvent.timestamp)).order_by('date').all()
        
        # Most active users
        top_users = db.query(
            User.email,
            User.full_name,
            func.count(AnalyticsEvent.id).label('activity_count')
        ).join(AnalyticsEvent).filter(
            AnalyticsEvent.timestamp >= start_date
        ).group_by(User.id).order_by(desc('activity_count')).limit(10).all()
        
        # Popular operations
        operation_stats = db.query(
            AnalyticsEvent.event_type,
            func.count(AnalyticsEvent.id).label('count')
        ).filter(
            AnalyticsEvent.timestamp >= start_date
        ).group_by(AnalyticsEvent.event_type).order_by(desc('count')).all()
        
        return {
            "hourly_usage": [{"hour": h.hour, "events": h.event_count} for h in hourly_usage],
            "daily_usage": [{"date": str(d.date), "events": d.event_count} for d in daily_usage],
            "top_users": [
                {
                    "email": u.email,
                    "name": u.full_name or "Unknown",
                    "activity_count": u.activity_count
                } for u in top_users
            ],
            "operation_stats": [
                {"operation": op.event_type, "count": op.count} for op in operation_stats
            ]
        }
    except Exception as e:
        logger.error(f"Error getting usage patterns: {e}")
        return {"error": str(e)}

def get_token_analytics(db: Session, days: int = 30) -> Dict[str, Any]:
    """Get detailed token usage analytics."""
    try:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        # Token usage by vendor
        vendor_usage = db.query(
            TokenUsage.vendor,
            func.sum(TokenUsage.total_tokens).label('total_tokens'),
            func.sum(TokenUsage.cost_estimate).label('total_cost'),
            func.count(TokenUsage.id).label('operation_count')
        ).filter(TokenUsage.timestamp >= start_date).group_by(TokenUsage.vendor).all()

        # Token usage by operation type
        operation_usage = db.query(
            TokenUsage.operation_type,
            func.sum(TokenUsage.total_tokens).label('total_tokens'),
            func.avg(TokenUsage.total_tokens).label('avg_tokens'),
            func.sum(TokenUsage.cost_estimate).label('total_cost')
        ).filter(TokenUsage.timestamp >= start_date).group_by(TokenUsage.operation_type).all()

        # Daily token usage trend
        daily_tokens = db.query(
            func.date(TokenUsage.timestamp).label('date'),
            func.sum(TokenUsage.total_tokens).label('total_tokens'),
            func.sum(TokenUsage.cost_estimate).label('total_cost')
        ).filter(TokenUsage.timestamp >= start_date).group_by(
            func.date(TokenUsage.timestamp)
        ).order_by('date').all()

        # Top token consuming users
        top_token_users = db.query(
            User.email,
            User.full_name,
            func.sum(TokenUsage.total_tokens).label('total_tokens'),
            func.sum(TokenUsage.cost_estimate).label('total_cost')
        ).join(TokenUsage).filter(
            TokenUsage.timestamp >= start_date
        ).group_by(User.id).order_by(desc('total_tokens')).limit(10).all()

        return {
            "vendor_usage": [
                {
                    "vendor": v.vendor,
                    "total_tokens": v.total_tokens,
                    "total_cost": round(v.total_cost, 4),
                    "operation_count": v.operation_count
                } for v in vendor_usage
            ],
            "operation_usage": [
                {
                    "operation": op.operation_type,
                    "total_tokens": op.total_tokens,
                    "avg_tokens": round(op.avg_tokens, 0),
                    "total_cost": round(op.total_cost, 4)
                } for op in operation_usage
            ],
            "daily_trend": [
                {
                    "date": str(d.date),
                    "tokens": d.total_tokens,
                    "cost": round(d.total_cost, 4)
                } for d in daily_tokens
            ],
            "top_users": [
                {
                    "email": u.email,
                    "name": u.full_name or "Unknown",
                    "total_tokens": u.total_tokens,
                    "total_cost": round(u.total_cost, 4)
                } for u in top_token_users
            ]
        }
    except Exception as e:
        logger.error(f"Error getting token analytics: {e}")
        return {"error": str(e)}

def get_performance_analytics(db: Session, days: int = 30) -> Dict[str, Any]:
    """Get performance analytics and response times."""
    try:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        # Performance by operation type - simplified approach
        operation_performance = db.query(
            PerformanceMetrics.operation_type,
            func.avg(PerformanceMetrics.duration_seconds).label('avg_duration'),
            func.min(PerformanceMetrics.duration_seconds).label('min_duration'),
            func.max(PerformanceMetrics.duration_seconds).label('max_duration'),
            func.count(PerformanceMetrics.id).label('operation_count')
        ).filter(
            PerformanceMetrics.timestamp >= start_date
        ).group_by(PerformanceMetrics.operation_type).all()

        # Get success counts separately for each operation type
        operation_success_counts = {}
        for op in operation_performance:
            success_count = db.query(func.count(PerformanceMetrics.id)).filter(
                and_(
                    PerformanceMetrics.timestamp >= start_date,
                    PerformanceMetrics.operation_type == op.operation_type,
                    PerformanceMetrics.success == True
                )
            ).scalar() or 0
            operation_success_counts[op.operation_type] = success_count

        # Performance trend over time
        daily_performance = db.query(
            func.date(PerformanceMetrics.timestamp).label('date'),
            func.avg(PerformanceMetrics.duration_seconds).label('avg_duration'),
            func.count(PerformanceMetrics.id).label('operation_count')
        ).filter(
            PerformanceMetrics.timestamp >= start_date
        ).group_by(func.date(PerformanceMetrics.timestamp)).order_by('date').all()

        # File size vs processing time correlation
        file_size_performance = db.query(
            PerformanceMetrics.file_size_bytes,
            PerformanceMetrics.duration_seconds
        ).filter(
            and_(
                PerformanceMetrics.timestamp >= start_date,
                PerformanceMetrics.file_size_bytes.isnot(None),
                PerformanceMetrics.operation_type == 'DOCUMENT_ANALYSIS'
            )
        ).all()

        # Error analysis - simplified approach
        error_analysis = db.query(
            PerformanceMetrics.operation_type,
            func.count(PerformanceMetrics.id).label('total_operations')
        ).filter(
            PerformanceMetrics.timestamp >= start_date
        ).group_by(PerformanceMetrics.operation_type).all()

        # Get error counts separately
        operation_error_counts = {}
        for op in error_analysis:
            error_count = db.query(func.count(PerformanceMetrics.id)).filter(
                and_(
                    PerformanceMetrics.timestamp >= start_date,
                    PerformanceMetrics.operation_type == op.operation_type,
                    PerformanceMetrics.success == False
                )
            ).scalar() or 0
            operation_error_counts[op.operation_type] = error_count

        return {
            "operation_performance": [
                {
                    "operation": op.operation_type,
                    "avg_duration": round(op.avg_duration, 2),
                    "min_duration": round(op.min_duration, 2),
                    "max_duration": round(op.max_duration, 2),
                    "operation_count": op.operation_count,
                    "success_rate": round((operation_success_counts.get(op.operation_type, 0) / op.operation_count * 100), 2)
                } for op in operation_performance
            ],
            "daily_performance": [
                {
                    "date": str(d.date),
                    "avg_duration": round(d.avg_duration, 2),
                    "operation_count": d.operation_count
                } for d in daily_performance
            ],
            "file_size_correlation": [
                {
                    "file_size_mb": round((f.file_size_bytes or 0) / (1024 * 1024), 2),
                    "duration_seconds": round(f.duration_seconds, 2)
                } for f in file_size_performance
            ],
            "error_rates": [
                {
                    "operation": err.operation_type,
                    "total_operations": err.total_operations,
                    "error_count": operation_error_counts.get(err.operation_type, 0),
                    "error_rate": round((operation_error_counts.get(err.operation_type, 0) / err.total_operations * 100), 2)
                } for err in error_analysis
            ]
        }
    except Exception as e:
        logger.error(f"Error getting performance analytics: {e}")
        return {"error": str(e)}

def get_user_satisfaction_analytics(db: Session, days: int = 30) -> Dict[str, Any]:
    """Get user satisfaction and feedback analytics."""
    try:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        # Overall satisfaction metrics - simplified approach
        satisfaction_stats = db.query(
            func.avg(UserFeedback.rating).label('avg_rating'),
            func.count(UserFeedback.id).label('total_feedback')
        ).filter(UserFeedback.timestamp >= start_date).first()

        # Get rating counts separately
        positive_ratings = db.query(func.count(UserFeedback.id)).filter(
            and_(UserFeedback.timestamp >= start_date, UserFeedback.rating >= 4)
        ).scalar() or 0

        negative_ratings = db.query(func.count(UserFeedback.id)).filter(
            and_(UserFeedback.timestamp >= start_date, UserFeedback.rating <= 2)
        ).scalar() or 0

        helpful_count = db.query(func.count(UserFeedback.id)).filter(
            and_(UserFeedback.timestamp >= start_date, UserFeedback.helpful == True)
        ).scalar() or 0

        unhelpful_count = db.query(func.count(UserFeedback.id)).filter(
            and_(UserFeedback.timestamp >= start_date, UserFeedback.helpful == False)
        ).scalar() or 0

        # Feedback by operation type
        feedback_by_type = db.query(
            UserFeedback.feedback_type,
            func.avg(UserFeedback.rating).label('avg_rating'),
            func.count(UserFeedback.id).label('feedback_count')
        ).filter(
            and_(
                UserFeedback.timestamp >= start_date,
                UserFeedback.rating.isnot(None)
            )
        ).group_by(UserFeedback.feedback_type).all()

        # Daily satisfaction trend
        daily_satisfaction = db.query(
            func.date(UserFeedback.timestamp).label('date'),
            func.avg(UserFeedback.rating).label('avg_rating'),
            func.count(UserFeedback.id).label('feedback_count')
        ).filter(
            and_(
                UserFeedback.timestamp >= start_date,
                UserFeedback.rating.isnot(None)
            )
        ).group_by(func.date(UserFeedback.timestamp)).order_by('date').all()

        # Recent comments
        recent_comments = db.query(
            UserFeedback.comment,
            UserFeedback.rating,
            UserFeedback.timestamp,
            User.email
        ).join(User).filter(
            and_(
                UserFeedback.timestamp >= start_date,
                UserFeedback.comment.isnot(None),
                UserFeedback.comment != ''
            )
        ).order_by(desc(UserFeedback.timestamp)).limit(20).all()

        total_feedback = satisfaction_stats.total_feedback or 0

        return {
            "overall_satisfaction": {
                "average_rating": round(satisfaction_stats.avg_rating or 0, 2),
                "total_feedback": total_feedback,
                "positive_rate": round(positive_ratings / max(total_feedback, 1) * 100, 2),
                "negative_rate": round(negative_ratings / max(total_feedback, 1) * 100, 2),
                "helpful_rate": round(
                    helpful_count / max(helpful_count + unhelpful_count, 1) * 100, 2
                )
            },
            "feedback_by_type": [
                {
                    "type": fb.feedback_type,
                    "avg_rating": round(fb.avg_rating, 2),
                    "count": fb.feedback_count
                } for fb in feedback_by_type
            ],
            "daily_satisfaction": [
                {
                    "date": str(d.date),
                    "avg_rating": round(d.avg_rating, 2),
                    "feedback_count": d.feedback_count
                } for d in daily_satisfaction
            ],
            "recent_comments": [
                {
                    "comment": c.comment,
                    "rating": c.rating,
                    "timestamp": c.timestamp.isoformat(),
                    "user_email": c.email
                } for c in recent_comments
            ]
        }
    except Exception as e:
        logger.error(f"Error getting user satisfaction analytics: {e}")
        return {"error": str(e)}

"""
Shared domain entities for the microservices architecture.
These represent the core business objects across all services.
"""

from abc import ABC
from datetime import datetime
from typing import Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum


class DocumentStatus(Enum):
    UPLOADED = "UPLOADED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    ERROR = "ERROR"
    CANCELLED = "CANCELLED"


class EventType(Enum):
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    DOCUMENT_UPLOAD = "DOCUMENT_UPLOAD"
    DOCUMENT_VIEW = "DOCUMENT_VIEW"
    ANALYSIS_START = "ANALYSIS_START"
    ANALYSIS_COMPLETE = "ANALYSIS_COMPLETE"
    QUESTION_ASK = "QUESTION_ASK"
    QUESTION_VIEW = "QUESTION_VIEW"
    FEEDBACK_SUBMIT = "FEEDBACK_SUBMIT"
    ADMIN_ACCESS = "ADMIN_ACCESS"
    SETTINGS_UPDATE = "SETTINGS_UPDATE"


@dataclass
class BaseEntity(ABC):
    """Base entity class with common fields."""
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class User(BaseEntity):
    """User domain entity."""
    email: str
    full_name: str
    is_active: bool = True
    is_admin: bool = False
    last_login: Optional[datetime] = None
    hashed_password: Optional[str] = None


@dataclass
class Document(BaseEntity):
    """Document domain entity."""
    filename: str
    file_path: str
    file_size: int
    mime_type: str
    owner_id: int
    status: DocumentStatus = DocumentStatus.UPLOADED


@dataclass
class AnalysisResult(BaseEntity):
    """Analysis result domain entity."""
    document_id: int
    summary: str
    key_insights: str
    financial_metrics: str
    risk_factors: str
    recommendations: str
    processing_time: Optional[float] = None


@dataclass
class QASession(BaseEntity):
    """Q&A session domain entity."""
    document_id: int


@dataclass
class Question(BaseEntity):
    """Question domain entity."""
    session_id: int
    question_text: str
    answer_text: str
    sources: str  # JSON string


@dataclass
class AnalyticsEvent(BaseEntity):
    """Analytics event domain entity."""
    user_id: int
    event_type: EventType
    event_data: Dict[str, Any]
    timestamp: datetime
    session_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


@dataclass
class TokenUsage(BaseEntity):
    """Token usage domain entity."""
    user_id: int
    operation_type: str
    model_name: str
    vendor: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    cost_estimate: float
    timestamp: datetime
    document_id: Optional[int] = None
    question_id: Optional[int] = None


@dataclass
class PerformanceMetrics(BaseEntity):
    """Performance metrics domain entity."""
    user_id: int
    operation_type: str
    start_time: datetime
    end_time: datetime
    duration_seconds: float
    success: bool
    document_id: Optional[int] = None
    question_id: Optional[int] = None
    file_size_bytes: Optional[int] = None
    error_message: Optional[str] = None


@dataclass
class UserFeedback(BaseEntity):
    """User feedback domain entity."""
    user_id: int
    feedback_type: str
    timestamp: datetime
    rating: Optional[int] = None
    comment: Optional[str] = None
    helpful: Optional[bool] = None
    question_id: Optional[int] = None
    document_id: Optional[int] = None


@dataclass
class LLMConfig(BaseEntity):
    """LLM configuration domain entity."""
    vendor: str
    api_key: Optional[str]
    base_url: str
    model: str
    temperature: float
    max_tokens: int
    timeout: int
    is_active: bool = True


@dataclass
class StorageInfo(BaseEntity):
    """Storage information domain entity."""
    user_id: int
    total_size: int
    document_count: int
    last_cleanup: Optional[datetime] = None

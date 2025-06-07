from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class UserCreate(BaseModel):
    email: str
    password: str
    full_name: Optional[str] = None

class UserResponse(BaseModel):
    id: int
    email: str
    full_name: Optional[str]
    is_active: bool
    is_admin: bool
    last_login: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

# Admin-specific schemas
class AdminUserCreate(BaseModel):
    email: str
    password: str
    full_name: Optional[str] = None
    is_active: bool = True
    is_admin: bool = False

class AdminUserUpdate(BaseModel):
    email: Optional[str] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None
    is_admin: Optional[bool] = None
    password: Optional[str] = None

class AdminUserResponse(BaseModel):
    id: int
    email: str
    full_name: Optional[str]
    is_active: bool
    is_admin: bool
    last_login: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    document_count: int = 0

    class Config:
        orm_mode = True

class AdminUserListResponse(BaseModel):
    users: List[AdminUserResponse]
    total: int
    page: int
    per_page: int
    total_pages: int

# LLM Configuration schemas
class LLMVendorConfig(BaseModel):
    vendor: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model: Optional[str] = None
    temperature: Optional[float] = 0.3
    max_tokens: Optional[int] = 2000
    timeout: Optional[int] = 300

class LLMConfigResponse(BaseModel):
    current_vendor: str
    current_model: Optional[str]
    current_config: Dict[str, Any]
    available_vendors: List[str]
    vendor_models: Dict[str, List[str]]
    status: str
    error: Optional[str] = None

class LLMModelListResponse(BaseModel):
    vendor: str
    models: List[str]
    error: Optional[str] = None

class Token(BaseModel):
    access_token: str
    token_type: str

class DocumentResponse(BaseModel):
    id: int
    filename: str
    file_size: int
    mime_type: str
    status: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

class AnalysisResultResponse(BaseModel):
    id: int
    summary: str
    key_figures: List[Dict[str, Any]]
    created_at: datetime
    
    class Config:
        orm_mode = True

class QuestionRequest(BaseModel):
    question: str

class QuestionResponse(BaseModel):
    id: int
    question_text: str
    answer_text: str
    sources: List[Dict[str, Any]]
    created_at: datetime
    
    class Config:
        orm_mode = True

class LLMStatusResponse(BaseModel):
    status: str
    mode: str
    model: Optional[str]
    error: Optional[str]
    base_url: Optional[str] = None
    provider: Optional[str] = None
    api_key_status: Optional[str] = None

class LLMModeRequest(BaseModel):
    mode: str
    api_key: Optional[str] = None
    model: Optional[str] = None
    base_url: Optional[str] = None

# Storage Management schemas
class StorageDirectoryInfo(BaseModel):
    path: str
    size_bytes: int
    size_formatted: str
    file_count: int
    exists: bool
    error: Optional[str] = None

class StorageOverviewResponse(BaseModel):
    total_size: int
    total_size_formatted: str
    total_files: int
    directories: Dict[str, StorageDirectoryInfo]
    last_updated: str
    error: Optional[str] = None

class UserStorageInfo(BaseModel):
    count: int
    total_size: int
    total_size_formatted: str

class UserStorageDetails(BaseModel):
    user_id: int
    email: str
    full_name: Optional[str]
    is_active: bool
    created_at: Optional[str]
    storage: Dict[str, Any]

class UserStorageResponse(BaseModel):
    users: List[UserStorageDetails]

class StorageCleanupResult(BaseModel):
    success: bool
    cleaned: Dict[str, int]
    errors: List[str]
    error: Optional[str] = None

# Analytics schemas
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

class FeedbackRequest(BaseModel):
    feedback_type: str  # RATING, COMMENT, THUMBS_UP, THUMBS_DOWN
    rating: Optional[int] = None  # 1-5 scale
    comment: Optional[str] = None
    helpful: Optional[bool] = None  # True for thumbs up, False for thumbs down
    question_id: Optional[int] = None
    document_id: Optional[int] = None

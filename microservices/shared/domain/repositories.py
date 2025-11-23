"""
Repository interfaces for the domain layer.
These define the contracts for data access without implementation details.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime

from .entities import (
    User, Document, AnalysisResult, QASession, Question,
    AnalyticsEvent, TokenUsage, PerformanceMetrics, UserFeedback,
    LLMConfig, StorageInfo, EventType
)


class IUserRepository(ABC):
    """User repository interface."""
    
    @abstractmethod
    def create(self, user: User) -> User:
        pass
    
    @abstractmethod
    def get_by_id(self, user_id: int) -> Optional[User]:
        pass
    
    @abstractmethod
    def get_by_email(self, email: str) -> Optional[User]:
        pass
    
    @abstractmethod
    def update(self, user: User) -> User:
        pass
    
    @abstractmethod
    def delete(self, user_id: int) -> bool:
        pass
    
    @abstractmethod
    def get_all(self, skip: int = 0, limit: int = 100) -> List[User]:
        pass
    
    @abstractmethod
    def get_count(self) -> int:
        pass


class IDocumentRepository(ABC):
    """Document repository interface."""
    
    @abstractmethod
    def create(self, document: Document) -> Document:
        pass
    
    @abstractmethod
    def get_by_id(self, document_id: int) -> Optional[Document]:
        pass
    
    @abstractmethod
    def get_by_user_id(self, user_id: int, skip: int = 0, limit: int = 100) -> List[Document]:
        pass
    
    @abstractmethod
    def update(self, document: Document) -> Document:
        pass
    
    @abstractmethod
    def delete(self, document_id: int) -> bool:
        pass
    
    @abstractmethod
    def get_count_by_user(self, user_id: int) -> int:
        pass


class IAnalysisRepository(ABC):
    """Analysis repository interface."""
    
    @abstractmethod
    def create_result(self, result: AnalysisResult) -> AnalysisResult:
        pass
    
    @abstractmethod
    def get_result_by_document_id(self, document_id: int) -> Optional[AnalysisResult]:
        pass
    
    @abstractmethod
    def create_qa_session(self, session: QASession) -> QASession:
        pass
    
    @abstractmethod
    def get_qa_session_by_id(self, session_id: int) -> Optional[QASession]:
        pass
    
    @abstractmethod
    def create_question(self, question: Question) -> Question:
        pass
    
    @abstractmethod
    def get_questions_by_session(self, session_id: int) -> List[Question]:
        pass


class IAnalyticsRepository(ABC):
    """Analytics repository interface."""
    
    @abstractmethod
    def create_event(self, event: AnalyticsEvent) -> AnalyticsEvent:
        pass
    
    @abstractmethod
    def get_events_by_user(self, user_id: int, start_date: datetime, end_date: datetime) -> List[AnalyticsEvent]:
        pass
    
    @abstractmethod
    def get_events_by_type(self, event_type: EventType, start_date: datetime, end_date: datetime) -> List[AnalyticsEvent]:
        pass
    
    @abstractmethod
    def create_token_usage(self, usage: TokenUsage) -> TokenUsage:
        pass
    
    @abstractmethod
    def get_token_usage_by_user(self, user_id: int, start_date: datetime, end_date: datetime) -> List[TokenUsage]:
        pass
    
    @abstractmethod
    def create_performance_metric(self, metric: PerformanceMetrics) -> PerformanceMetrics:
        pass
    
    @abstractmethod
    def get_performance_metrics(self, start_date: datetime, end_date: datetime) -> List[PerformanceMetrics]:
        pass
    
    @abstractmethod
    def create_feedback(self, feedback: UserFeedback) -> UserFeedback:
        pass
    
    @abstractmethod
    def get_feedback_by_user(self, user_id: int) -> List[UserFeedback]:
        pass


class IStorageRepository(ABC):
    """Storage repository interface."""
    
    @abstractmethod
    def upload_file(self, file_path: str, content: bytes, content_type: str) -> bool:
        pass
    
    @abstractmethod
    def download_file(self, file_path: str) -> Optional[bytes]:
        pass
    
    @abstractmethod
    def delete_file(self, file_path: str) -> bool:
        pass
    
    @abstractmethod
    def get_file_info(self, file_path: str) -> Optional[Dict[str, Any]]:
        pass
    
    @abstractmethod
    def list_user_files(self, user_id: int) -> List[str]:
        pass
    
    @abstractmethod
    def get_storage_info(self, user_id: int) -> StorageInfo:
        pass


class ILLMConfigRepository(ABC):
    """LLM configuration repository interface."""
    
    @abstractmethod
    def get_config(self) -> Optional[LLMConfig]:
        pass
    
    @abstractmethod
    def save_config(self, config: LLMConfig) -> LLMConfig:
        pass
    
    @abstractmethod
    def test_connection(self, config: LLMConfig) -> bool:
        pass

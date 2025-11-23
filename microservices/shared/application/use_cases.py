"""
Application use cases (business logic) for the microservices.
These implement the core business rules and orchestrate domain operations.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from ..domain.entities import (
    User, Document, AnalysisResult, QASession, Question,
    AnalyticsEvent, TokenUsage, PerformanceMetrics, UserFeedback,
    LLMConfig, StorageInfo, EventType, DocumentStatus
)
from ..domain.repositories import (
    IUserRepository, IDocumentRepository, IAnalysisRepository,
    IAnalyticsRepository, IStorageRepository, ILLMConfigRepository
)


class BaseUseCase(ABC):
    """Base use case class."""
    pass


# User Service Use Cases
class CreateUserUseCase(BaseUseCase):
    def __init__(self, user_repo: IUserRepository):
        self.user_repo = user_repo
    
    def execute(self, email: str, password: str, full_name: str, is_admin: bool = False) -> User:
        # Check if user already exists
        existing_user = self.user_repo.get_by_email(email)
        if existing_user:
            raise ValueError("User with this email already exists")
        
        # Create new user
        user = User(
            email=email,
            full_name=full_name,
            is_admin=is_admin,
            hashed_password=self._hash_password(password),
            created_at=datetime.utcnow()
        )
        
        return self.user_repo.create(user)
    
    def _hash_password(self, password: str) -> str:
        # Implement password hashing
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        return pwd_context.hash(password)


class AuthenticateUserUseCase(BaseUseCase):
    def __init__(self, user_repo: IUserRepository):
        self.user_repo = user_repo
    
    def execute(self, email: str, password: str) -> Optional[User]:
        user = self.user_repo.get_by_email(email)
        if not user or not self._verify_password(password, user.hashed_password):
            return None
        
        # Update last login
        user.last_login = datetime.utcnow()
        return self.user_repo.update(user)
    
    def _verify_password(self, plain_password: str, hashed_password: str) -> bool:
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        return pwd_context.verify(plain_password, hashed_password)


# Document Service Use Cases
class UploadDocumentUseCase(BaseUseCase):
    def __init__(self, document_repo: IDocumentRepository, storage_repo: IStorageRepository):
        self.document_repo = document_repo
        self.storage_repo = storage_repo
    
    def execute(self, user_id: int, filename: str, content: bytes, content_type: str) -> Document:
        # Generate file path
        file_path = f"users/{user_id}/documents/{filename}"
        
        # Upload to storage
        if not self.storage_repo.upload_file(file_path, content, content_type):
            raise RuntimeError("Failed to upload file to storage")
        
        # Create document record
        document = Document(
            filename=filename,
            file_path=file_path,
            file_size=len(content),
            mime_type=content_type,
            owner_id=user_id,
            status=DocumentStatus.UPLOADED,
            created_at=datetime.utcnow()
        )
        
        return self.document_repo.create(document)


class GetUserDocumentsUseCase(BaseUseCase):
    def __init__(self, document_repo: IDocumentRepository):
        self.document_repo = document_repo
    
    def execute(self, user_id: int, skip: int = 0, limit: int = 100) -> List[Document]:
        return self.document_repo.get_by_user_id(user_id, skip, limit)


# Analysis Service Use Cases
class AnalyzeDocumentUseCase(BaseUseCase):
    def __init__(self, 
                 document_repo: IDocumentRepository,
                 analysis_repo: IAnalysisRepository,
                 storage_repo: IStorageRepository,
                 llm_config_repo: ILLMConfigRepository):
        self.document_repo = document_repo
        self.analysis_repo = analysis_repo
        self.storage_repo = storage_repo
        self.llm_config_repo = llm_config_repo
    
    def execute(self, document_id: int) -> AnalysisResult:
        # Get document
        document = self.document_repo.get_by_id(document_id)
        if not document:
            raise ValueError("Document not found")
        
        # Update document status
        document.status = DocumentStatus.PROCESSING
        self.document_repo.update(document)
        
        try:
            # Get file content
            content = self.storage_repo.download_file(document.file_path)
            if not content:
                raise RuntimeError("Failed to download file content")
            
            # Get LLM config
            llm_config = self.llm_config_repo.get_config()
            if not llm_config:
                raise RuntimeError("LLM configuration not found")
            
            # Perform analysis (simplified)
            analysis_result = self._analyze_content(content, llm_config)
            
            # Save analysis result
            result = AnalysisResult(
                document_id=document_id,
                summary=analysis_result["summary"],
                key_insights=analysis_result["key_insights"],
                financial_metrics=analysis_result["financial_metrics"],
                risk_factors=analysis_result["risk_factors"],
                recommendations=analysis_result["recommendations"],
                processing_time=analysis_result["processing_time"],
                created_at=datetime.utcnow()
            )
            
            saved_result = self.analysis_repo.create_result(result)
            
            # Update document status
            document.status = DocumentStatus.COMPLETED
            self.document_repo.update(document)
            
            return saved_result
            
        except Exception as e:
            # Update document status to error
            document.status = DocumentStatus.ERROR
            self.document_repo.update(document)
            raise e
    
    def _analyze_content(self, content: bytes, llm_config: LLMConfig) -> Dict[str, Any]:
        # Simplified analysis - in real implementation, use LLM
        return {
            "summary": "Financial document analysis summary",
            "key_insights": "Key financial insights",
            "financial_metrics": "Financial metrics analysis",
            "risk_factors": "Risk factors identified",
            "recommendations": "Recommendations based on analysis",
            "processing_time": 30.0
        }


class AskQuestionUseCase(BaseUseCase):
    def __init__(self, 
                 analysis_repo: IAnalysisRepository,
                 document_repo: IDocumentRepository,
                 storage_repo: IStorageRepository,
                 llm_config_repo: ILLMConfigRepository):
        self.analysis_repo = analysis_repo
        self.document_repo = document_repo
        self.storage_repo = storage_repo
        self.llm_config_repo = llm_config_repo
    
    def execute(self, document_id: int, question_text: str) -> Question:
        # Get or create QA session
        session = QASession(
            document_id=document_id,
            created_at=datetime.utcnow()
        )
        session = self.analysis_repo.create_qa_session(session)
        
        # Get LLM config and generate answer
        llm_config = self.llm_config_repo.get_config()
        answer_data = self._generate_answer(question_text, document_id, llm_config)
        
        # Create question record
        question = Question(
            session_id=session.id,
            question_text=question_text,
            answer_text=answer_data["answer"],
            sources=answer_data["sources"],
            created_at=datetime.utcnow()
        )
        
        return self.analysis_repo.create_question(question)
    
    def _generate_answer(self, question: str, document_id: int, llm_config: LLMConfig) -> Dict[str, str]:
        # Simplified answer generation
        return {
            "answer": f"Answer to: {question}",
            "sources": '[]'
        }


# Analytics Service Use Cases
class TrackEventUseCase(BaseUseCase):
    def __init__(self, analytics_repo: IAnalyticsRepository):
        self.analytics_repo = analytics_repo
    
    def execute(self, user_id: int, event_type: EventType, event_data: Dict[str, Any], 
                session_id: str = None, ip_address: str = None, user_agent: str = None) -> AnalyticsEvent:
        event = AnalyticsEvent(
            user_id=user_id,
            event_type=event_type,
            event_data=event_data,
            timestamp=datetime.utcnow(),
            session_id=session_id,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return self.analytics_repo.create_event(event)


class GetAnalyticsOverviewUseCase(BaseUseCase):
    def __init__(self, analytics_repo: IAnalyticsRepository, user_repo: IUserRepository):
        self.analytics_repo = analytics_repo
        self.user_repo = user_repo
    
    def execute(self, days: int = 30) -> Dict[str, Any]:
        start_date = datetime.utcnow() - timedelta(days=days)
        end_date = datetime.utcnow()
        
        # Get analytics data
        events = self.analytics_repo.get_events_by_type(None, start_date, end_date)
        token_usage = self.analytics_repo.get_token_usage_by_user(None, start_date, end_date)
        performance_metrics = self.analytics_repo.get_performance_metrics(start_date, end_date)
        
        # Calculate overview metrics
        return {
            "period_days": days,
            "total_events": len(events),
            "total_tokens": sum(usage.total_tokens for usage in token_usage),
            "total_cost": sum(usage.cost_estimate for usage in token_usage),
            "avg_response_time": sum(metric.duration_seconds for metric in performance_metrics) / len(performance_metrics) if performance_metrics else 0,
            "active_users": len(set(event.user_id for event in events))
        }

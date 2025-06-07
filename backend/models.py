from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    full_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    last_login = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    documents = relationship("Document", back_populates="owner", cascade="all, delete-orphan")

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String)
    file_path = Column(String)
    file_size = Column(Integer)
    mime_type = Column(String)
    status = Column(String, default="UPLOADED")  # UPLOADED, PROCESSING, COMPLETED, ERROR, CANCELLED
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    owner_id = Column(Integer, ForeignKey("users.id"))
    
    owner = relationship("User", back_populates="documents")
    analysis_results = relationship("AnalysisResult", back_populates="document", cascade="all, delete-orphan")
    qa_sessions = relationship("QASession", back_populates="document", cascade="all, delete-orphan")

class AnalysisResult(Base):
    __tablename__ = "analysis_results"
    
    id = Column(Integer, primary_key=True, index=True)
    summary = Column(Text)
    key_figures = Column(Text)  # JSON string
    vector_db_path = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    document_id = Column(Integer, ForeignKey("documents.id"))
    
    document = relationship("Document", back_populates="analysis_results")

class QASession(Base):
    __tablename__ = "qa_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    document_id = Column(Integer, ForeignKey("documents.id"))
    
    document = relationship("Document", back_populates="qa_sessions")
    questions = relationship("Question", back_populates="session", cascade="all, delete-orphan")

class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    question_text = Column(Text)
    answer_text = Column(Text)
    sources = Column(Text)  # JSON string
    created_at = Column(DateTime, default=datetime.utcnow)
    session_id = Column(Integer, ForeignKey("qa_sessions.id"))

    session = relationship("QASession", back_populates="questions")

# Analytics Models
class AnalyticsEvent(Base):
    __tablename__ = "analytics_events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    event_type = Column(String)  # LOGIN, DOCUMENT_UPLOAD, ANALYSIS_START, ANALYSIS_COMPLETE, QUESTION_ASK, etc.
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
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=True)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=True)
    operation_type = Column(String)  # ANALYSIS, QUESTION, EMBEDDING, SUMMARY
    model_name = Column(String)
    vendor = Column(String)
    input_tokens = Column(Integer, default=0)
    output_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    cost_estimate = Column(Float, default=0.0)  # Estimated cost in USD
    timestamp = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")
    document = relationship("Document")
    question = relationship("Question")

class PerformanceMetrics(Base):
    __tablename__ = "performance_metrics"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=True)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=True)
    operation_type = Column(String)  # DOCUMENT_ANALYSIS, EMBEDDING_CREATION, QUESTION_ANSWERING
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    duration_seconds = Column(Float)
    file_size_bytes = Column(Integer, nullable=True)
    success = Column(Boolean, default=True)
    error_message = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")
    document = relationship("Document")
    question = relationship("Question")

class UserFeedback(Base):
    __tablename__ = "user_feedback"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=True)
    feedback_type = Column(String)  # RATING, COMMENT, THUMBS_UP, THUMBS_DOWN
    rating = Column(Integer, nullable=True)  # 1-5 scale
    comment = Column(Text, nullable=True)
    helpful = Column(Boolean, nullable=True)  # True for thumbs up, False for thumbs down
    timestamp = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")
    question = relationship("Question")
    document = relationship("Document")

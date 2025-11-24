from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True, nullable=False)
    original_filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String, nullable=False)
    status = Column(String, default="UPLOADED", index=True)  # UPLOADED, PROCESSING, COMPLETED, ERROR
    owner_id = Column(Integer, nullable=False)  # Would be ForeignKey in full implementation
    vector_db_path = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)

class AnalysisResult(Base):
    __tablename__ = "analysis_results"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, nullable=False)  # Would be ForeignKey in full implementation
    summary = Column(Text, nullable=True)
    key_figures = Column(Text, nullable=True)  # JSON string
    vector_db_path = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Question(Base):
    __tablename__ = "questions"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, nullable=False)  # Would be ForeignKey in full implementation
    question_text = Column(String, nullable=False)
    answer_text = Column(Text, nullable=False)
    sources = Column(Text, nullable=True)  # JSON string
    created_at = Column(DateTime, default=datetime.utcnow)
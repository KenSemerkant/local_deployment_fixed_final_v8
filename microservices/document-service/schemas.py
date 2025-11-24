from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

# User schemas
class UserBase(BaseModel):
    email: str
    full_name: Optional[str] = None
    is_active: bool = True
    is_admin: bool = False

class UserCreate(UserBase):
    password: str

class UserUpdate(UserBase):
    password: Optional[str] = None

class UserResponse(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

# Document schemas
class DocumentBase(BaseModel):
    filename: str
    original_filename: str
    file_path: str
    file_size: int
    mime_type: str
    status: str = "UPLOADED"
    owner_id: int

class DocumentCreate(DocumentBase):
    pass

class DocumentUpdate(BaseModel):
    status: Optional[str] = None

class DocumentResponse(DocumentBase):
    id: int
    created_at: datetime
    updated_at: datetime
    uploaded_at: datetime
    processed_at: Optional[datetime] = None
    vector_db_path: Optional[str] = None

    class Config:
        orm_mode = True

# Analysis schemas
class KeyFigure(BaseModel):
    name: str
    value: str
    source_page: Optional[int] = None
    source_section: Optional[str] = None

class SourceReference(BaseModel):
    page: Optional[int] = None
    snippet: Optional[str] = None
    section: Optional[str] = None

class AnalysisResult(BaseModel):
    id: int
    document_id: int
    summary: Optional[str] = None
    key_figures: Optional[List[Dict[str, Any]]] = None
    vector_db_path: Optional[str] = None
    created_at: datetime

    class Config:
        orm_mode = True

class AnalysisRequest(BaseModel):
    document_id: int

class QuestionResponse(BaseModel):
    id: int
    document_id: int
    question_text: str
    answer_text: str
    sources: List[Dict[str, Any]]
    created_at: datetime

    class Config:
        orm_mode = True

class QuestionRequest(BaseModel):
    question: str
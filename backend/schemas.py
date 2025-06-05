from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class UserCreate(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    id: int
    email: str
    created_at: datetime
    
    class Config:
        orm_mode = True

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

class LLMModeRequest(BaseModel):
    mode: str
    api_key: Optional[str] = None
    model: Optional[str] = None

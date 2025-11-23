"""
Domain entities for the Document Service.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from enum import Enum


class DocumentStatus(Enum):
    UPLOADED = "UPLOADED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    ERROR = "ERROR"
    CANCELLED = "CANCELLED"


@dataclass
class Document:
    """Document domain entity."""
    filename: str
    file_path: str
    file_size: int
    mime_type: str
    owner_id: int
    status: DocumentStatus = DocumentStatus.UPLOADED
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()

"""
Repository interfaces for the Document Service.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from .entities import Document


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
    def get_all(self, skip: int = 0, limit: int = 100) -> List[Document]:
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

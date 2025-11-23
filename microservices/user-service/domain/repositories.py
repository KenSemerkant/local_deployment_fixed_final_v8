"""
Repository interfaces for the User Service domain layer.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from .entities import User


class IUserRepository(ABC):
    """User repository interface."""
    
    @abstractmethod
    def create(self, user: User) -> User:
        """Create a new user."""
        pass
    
    @abstractmethod
    def get_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        pass
    
    @abstractmethod
    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        pass
    
    @abstractmethod
    def update(self, user: User) -> User:
        """Update user."""
        pass
    
    @abstractmethod
    def delete(self, user_id: int) -> bool:
        """Delete user."""
        pass
    
    @abstractmethod
    def get_all(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Get all users with pagination."""
        pass
    
    @abstractmethod
    def get_count(self) -> int:
        """Get total user count."""
        pass

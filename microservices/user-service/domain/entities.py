"""
Domain entities for the User Service.
These represent the core business objects and rules.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class User:
    """User domain entity."""
    email: str
    full_name: str
    hashed_password: str
    is_active: bool = True
    is_admin: bool = False
    id: Optional[int] = None
    last_login: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()
    
    def is_authenticated(self) -> bool:
        """Check if user is authenticated."""
        return self.is_active
    
    def has_admin_privileges(self) -> bool:
        """Check if user has admin privileges."""
        return self.is_admin and self.is_active
    
    def update_last_login(self):
        """Update last login timestamp."""
        self.last_login = datetime.utcnow()
        self.updated_at = datetime.utcnow()

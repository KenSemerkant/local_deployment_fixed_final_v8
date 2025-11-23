"""
Pydantic schemas for the User Service API.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr

from domain.entities import User


class UserBase(BaseModel):
    """Base user schema."""
    email: EmailStr
    full_name: str


class UserCreate(UserBase):
    """Schema for creating a user."""
    password: str


class AdminUserCreate(UserCreate):
    """Schema for admin creating a user."""
    is_admin: bool = False


class AdminUserUpdate(BaseModel):
    """Schema for admin updating a user."""
    full_name: Optional[str] = None
    is_active: Optional[bool] = None
    is_admin: Optional[bool] = None


class UserResponse(UserBase):
    """Schema for user response."""
    id: int
    is_active: bool
    is_admin: bool
    last_login: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
    
    @classmethod
    def from_entity(cls, user: User) -> "UserResponse":
        """Create response from domain entity."""
        return cls(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            is_active=user.is_active,
            is_admin=user.is_admin,
            last_login=user.last_login,
            created_at=user.created_at,
            updated_at=user.updated_at
        )


class Token(BaseModel):
    """Token response schema."""
    access_token: str
    token_type: str


class TokenData(BaseModel):
    """Token data schema."""
    email: Optional[str] = None

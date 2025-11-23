"""
Repository implementations for the User Service.
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from domain.entities import User
from domain.repositories import IUserRepository
from .database import UserModel


class SQLAlchemyUserRepository(IUserRepository):
    """SQLAlchemy implementation of the user repository."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, user: User) -> User:
        """Create a new user."""
        db_user = UserModel(
            email=user.email,
            hashed_password=user.hashed_password,
            full_name=user.full_name,
            is_active=user.is_active,
            is_admin=user.is_admin,
            created_at=user.created_at or datetime.utcnow(),
            updated_at=user.updated_at or datetime.utcnow()
        )
        
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        
        return self._to_entity(db_user)
    
    def get_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        db_user = self.db.query(UserModel).filter(UserModel.id == user_id).first()
        return self._to_entity(db_user) if db_user else None
    
    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        db_user = self.db.query(UserModel).filter(UserModel.email == email).first()
        return self._to_entity(db_user) if db_user else None
    
    def update(self, user: User) -> User:
        """Update user."""
        db_user = self.db.query(UserModel).filter(UserModel.id == user.id).first()
        if not db_user:
            raise ValueError("User not found")
        
        db_user.email = user.email
        db_user.hashed_password = user.hashed_password
        db_user.full_name = user.full_name
        db_user.is_active = user.is_active
        db_user.is_admin = user.is_admin
        db_user.last_login = user.last_login
        db_user.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(db_user)
        
        return self._to_entity(db_user)
    
    def delete(self, user_id: int) -> bool:
        """Delete user."""
        db_user = self.db.query(UserModel).filter(UserModel.id == user_id).first()
        if not db_user:
            return False
        
        self.db.delete(db_user)
        self.db.commit()
        return True
    
    def get_all(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Get all users with pagination."""
        db_users = self.db.query(UserModel).offset(skip).limit(limit).all()
        return [self._to_entity(db_user) for db_user in db_users]
    
    def get_count(self) -> int:
        """Get total user count."""
        return self.db.query(UserModel).count()
    
    def _to_entity(self, db_user: UserModel) -> User:
        """Convert database model to domain entity."""
        return User(
            id=db_user.id,
            email=db_user.email,
            hashed_password=db_user.hashed_password,
            full_name=db_user.full_name,
            is_active=db_user.is_active,
            is_admin=db_user.is_admin,
            last_login=db_user.last_login,
            created_at=db_user.created_at,
            updated_at=db_user.updated_at
        )

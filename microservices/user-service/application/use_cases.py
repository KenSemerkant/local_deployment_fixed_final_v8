"""
Application use cases for the User Service.
Contains the business logic and orchestrates domain operations.
"""

from datetime import datetime
from typing import Optional
from passlib.context import CryptContext

from domain.entities import User
from domain.repositories import IUserRepository


class CreateUserUseCase:
    """Use case for creating a new user."""
    
    def __init__(self, user_repository: IUserRepository):
        self.user_repository = user_repository
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    def execute(self, email: str, password: str, full_name: str, is_admin: bool = False) -> User:
        """Create a new user."""
        # Check if user already exists
        existing_user = self.user_repository.get_by_email(email)
        if existing_user:
            raise ValueError("User with this email already exists")
        
        # Hash password
        hashed_password = self.pwd_context.hash(password)
        
        # Create user entity
        user = User(
            email=email,
            full_name=full_name,
            hashed_password=hashed_password,
            is_admin=is_admin,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Save user
        return self.user_repository.create(user)


class AuthenticateUserUseCase:
    """Use case for authenticating a user."""
    
    def __init__(self, user_repository: IUserRepository):
        self.user_repository = user_repository
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    def execute(self, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password."""
        # Get user by email
        user = self.user_repository.get_by_email(email)
        if not user:
            return None
        
        # Verify password
        if not self.pwd_context.verify(password, user.hashed_password):
            return None
        
        # Check if user is active
        if not user.is_active:
            return None
        
        # Update last login
        user.update_last_login()
        self.user_repository.update(user)
        
        return user


class GetUserUseCase:
    """Use case for retrieving user information."""
    
    def __init__(self, user_repository: IUserRepository):
        self.user_repository = user_repository
    
    def execute_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        return self.user_repository.get_by_id(user_id)
    
    def execute_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        return self.user_repository.get_by_email(email)


class UpdateUserUseCase:
    """Use case for updating user information."""
    
    def __init__(self, user_repository: IUserRepository):
        self.user_repository = user_repository
    
    def execute(self, user_id: int, **updates) -> Optional[User]:
        """Update user information."""
        user = self.user_repository.get_by_id(user_id)
        if not user:
            return None
        
        # Update fields
        for field, value in updates.items():
            if hasattr(user, field) and value is not None:
                setattr(user, field, value)
        
        user.updated_at = datetime.utcnow()
        return self.user_repository.update(user)


class DeleteUserUseCase:
    """Use case for deleting a user."""
    
    def __init__(self, user_repository: IUserRepository):
        self.user_repository = user_repository
    
    def execute(self, user_id: int) -> bool:
        """Delete user by ID."""
        return self.user_repository.delete(user_id)

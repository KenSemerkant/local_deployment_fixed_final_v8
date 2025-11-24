from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from datetime import timedelta
import os

# Database configuration
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./auth.db")
engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# JWT configuration
JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "your-default-secret-key-change-this-in-production")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# Global constants
MOCK_DELAY = int(os.environ.get("MOCK_DELAY", "2"))
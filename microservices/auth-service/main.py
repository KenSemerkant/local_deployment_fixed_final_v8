from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordRequestForm, HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import os
import jwt
from datetime import datetime, timedelta
import hashlib
import sqlite3
from passlib.context import CryptContext

# Configure password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT configuration
SECRET_KEY = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Database configuration
DB_PATH = os.getenv("DATABASE_URL", "sqlite:///./auth.db")

class UserCreate(BaseModel):
    email: str
    password: str
    full_name: Optional[str] = None

class User(BaseModel):
    id: int
    email: str
    full_name: Optional[str] = None
    is_active: bool = True
    is_admin: bool = False

class UserInDB(User):
    hashed_password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

# OpenTelemetry tracing setup
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor

# Configure OpenTelemetry
otel_endpoint = os.getenv("OTEL_EXPORTER_OTLP_TRACES_ENDPOINT", "http://jaeger:4318/v1/traces")
service_name = os.getenv("OTEL_SERVICE_NAME", "auth_service")

# Set up the tracer
trace.set_tracer_provider(TracerProvider())
tracer = trace.get_tracer(__name__)

# Add OTLP span processor
span_processor = BatchSpanProcessor(
    OTLPSpanExporter(endpoint=otel_endpoint)
)
trace.get_tracer_provider().add_span_processor(span_processor)

# Initialize FastAPI app
app = FastAPI(title="Auth Service", version="1.0.0")

# Enable tracing for the FastAPI app
FastAPIInstrumentor.instrument_app(app)

# Instrument other libraries
RequestsInstrumentor().instrument()
LoggingInstrumentor().instrument()

# Initialize OAuth2 scheme
oauth2_scheme = HTTPBearer()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db_connection():
    """Create a database connection"""
    conn = sqlite3.connect(DB_PATH.replace("sqlite:///", ""))
    conn.row_factory = sqlite3.Row  # Enable column access by name
    return conn

def create_tables():
    """Create required database tables"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            hashed_password TEXT NOT NULL,
            full_name TEXT,
            is_active BOOLEAN DEFAULT 1,
            is_admin BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create demo user if doesn't exist
    cursor.execute("SELECT id FROM users WHERE email = ?", ("demo@example.com",))
    if cursor.fetchone() is None:
        hashed_password = pwd_context.hash("demo123")
        cursor.execute("""
            INSERT INTO users (email, hashed_password, full_name, is_active, is_admin)
            VALUES (?, ?, ?, ?, ?)
        """, ("demo@example.com", hashed_password, "Demo User", True, False))
    
    # Create admin user if doesn't exist
    cursor.execute("SELECT id FROM users WHERE email = ?", ("admin@example.com",))
    if cursor.fetchone() is None:
        hashed_password = pwd_context.hash("admin123")
        cursor.execute("""
            INSERT INTO users (email, hashed_password, full_name, is_active, is_admin)
            VALUES (?, ?, ?, ?, ?)
        """, ("admin@example.com", hashed_password, "Admin User", True, True))
    
    conn.commit()
    conn.close()

def verify_password(plain_password, hashed_password):
    """Verify a plain password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    """Hash a password"""
    return pwd_context.hash(password)

def get_user_by_email(email: str):
    """Get a user by email from the database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    user_row = cursor.fetchone()
    conn.close()

    if user_row:
        return UserInDB(
            id=user_row["id"],
            email=user_row["email"],
            full_name=user_row["full_name"],
            is_active=bool(user_row["is_active"]),
            is_admin=bool(user_row["is_admin"]),
            hashed_password=user_row["hashed_password"]
        )
    return None

def authenticate_user(email: str, password: str):
    """Authenticate a user"""
    user = get_user_by_email(email)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    # Return the user as a User model (without hashed_password)
    return User(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        is_admin=user.is_admin
    )

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(oauth2_scheme)):
    """Get current user from JWT token"""
    token = credentials.credentials
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except jwt.PyJWTError:
        raise credentials_exception

    user = get_user_by_email(email=token_data.email)
    if user is None:
        raise credentials_exception

    return user

@app.on_event("startup")
def startup_event():
    """Initialize database tables on startup"""
    create_tables()

@app.get("/")
def root():
    return {"message": "Auth Service", "version": "1.0.0"}

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "auth-service"}

@app.post("/token", response_model=Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/users", response_model=User)
def register_user(user: UserCreate):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if user already exists
    cursor.execute("SELECT id FROM users WHERE email = ?", (user.email,))
    if cursor.fetchone():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create new user
    hashed_password = get_password_hash(user.password)
    cursor.execute("""
        INSERT INTO users (email, hashed_password, full_name)
        VALUES (?, ?, ?)
    """, (user.email, hashed_password, user.full_name))
    
    user_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    # Return the created user
    return get_user_by_email(user.email)

@app.get("/users/me", response_model=User)
def read_users_me(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return current_user

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
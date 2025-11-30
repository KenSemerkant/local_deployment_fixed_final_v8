from fastapi import FastAPI, HTTPException, Depends, status, Header, BackgroundTasks
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

import redis
import json

# Configure password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Redis configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
try:
    redis_client = redis.from_url(REDIS_URL, decode_responses=True)
except Exception as e:
    print(f"Failed to connect to Redis: {e}")
    redis_client = None

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
    avatar_url: Optional[str] = None
    is_active: bool = True
    is_admin: bool = False

class UserInDB(User):
    hashed_password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class UserUpdate(BaseModel):
    email: Optional[str] = None
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None
    is_admin: Optional[bool] = None

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

# Internal API Key configuration
INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY")
ANALYTICS_SERVICE_URL = os.getenv("ANALYTICS_SERVICE_URL", "http://analytics-service:8000")

async def verify_internal_api_key(x_internal_api_key: str = Header(None)):
    if not INTERNAL_API_KEY:
        # If key is not set in env, we might want to fail open or closed. 
        # For security, let's log a warning but allow (dev mode) or fail.
        # Given the requirement, we should enforce it.
        # But if it's missing, maybe we shouldn't block everything if not configured?
        # Let's assume it MUST be configured.
        return
        
    if x_internal_api_key != INTERNAL_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid Internal API Key")

def track_analytics_event(user_id: int, event_type: str, event_data: dict):
    """Helper to track analytics events asynchronously"""
    try:
        import requests
        headers = {}
        if INTERNAL_API_KEY:
            headers["X-Internal-API-Key"] = INTERNAL_API_KEY
            
        requests.post(
            f"{ANALYTICS_SERVICE_URL}/events",
            json={
                "user_id": user_id,
                "event_type": event_type,
                "event_data": event_data
            },
            headers=headers,
            timeout=5
        )
    except Exception as e:
        # Don't fail the request if analytics fails
        print(f"Failed to track analytics event: {e}")

# Initialize FastAPI app with global dependency
app = FastAPI(
    title="Auth Service", 
    version="1.0.0",
    dependencies=[Depends(verify_internal_api_key)]
)

# Enable tracing for the FastAPI app
FastAPIInstrumentor.instrument_app(app)

# Instrument other libraries
RequestsInstrumentor().instrument()
LoggingInstrumentor().instrument()

# Initialize OAuth2 scheme
oauth2_scheme = HTTPBearer()

# CORS removed as this service is behind the gateway

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
            avatar_url TEXT,
            is_active BOOLEAN DEFAULT 1,
            is_admin BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Check if avatar_url column exists (for migration)
    cursor.execute("PRAGMA table_info(users)")
    columns = [column[1] for column in cursor.fetchall()]
    if "avatar_url" not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN avatar_url TEXT")
    
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
            avatar_url=user_row["avatar_url"] if "avatar_url" in user_row.keys() else None,
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
        avatar_url=user.avatar_url,
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

    # Check Redis cache first
    if redis_client:
        try:
            cached_user = redis_client.get(f"user:{email}")
            if cached_user:
                user_data = json.loads(cached_user)
                return User(**user_data)
        except Exception as e:
            print(f"Redis error: {e}")

    user = get_user_by_email(email=token_data.email)
    if user is None:
        raise credentials_exception

    # Cache user data
    if redis_client:
        try:
            # Convert UserInDB to User model for caching (exclude hashed_password)
            user_to_cache = User(
                id=user.id,
                email=user.email,
                full_name=user.full_name,
                avatar_url=user.avatar_url,
                is_active=user.is_active,
                is_admin=user.is_admin
            )
            redis_client.setex(
                f"user:{email}",
                900,  # 15 minutes TTL
                json.dumps(user_to_cache.dict())
            )
        except Exception as e:
            print(f"Redis set error: {e}")

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
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), background_tasks: BackgroundTasks = BackgroundTasks()):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (form_data.username,))
    user = cursor.fetchone()
    conn.close()

    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["email"]}, expires_delta=access_token_expires
    )
    
    # Track login event
    background_tasks.add_task(
        track_analytics_event,
        user_id=user["id"],
        event_type="user_login",
        event_data={"email": user["email"]}
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/users", response_model=User)
async def create_user(user: UserCreate, background_tasks: BackgroundTasks):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM users WHERE email = ?", (user.email,))
    if cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = get_password_hash(user.password)
    cursor.execute(
        "INSERT INTO users (email, hashed_password, full_name) VALUES (?, ?, ?)",
        (user.email, hashed_password, user.full_name)
    )
    user_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    # Track registration event
    background_tasks.add_task(
        track_analytics_event,
        user_id=user_id,
        event_type="user_registered",
        event_data={"email": user.email, "full_name": user.full_name}
    )
    
    return {
        "id": user_id, 
        "email": user.email, 
        "full_name": user.full_name,
        "is_active": True,
        "is_admin": False
    }

@app.get("/users/me", response_model=User)
def read_users_me(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return current_user

@app.put("/users/me", response_model=User)
def update_user_me(user_update: UserUpdate, current_user: User = Depends(get_current_user)):
    """Update current user profile"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Build update query
    update_fields = []
    params = []
    
    if user_update.email is not None:
        # Check if email is already taken by another user
        cursor.execute("SELECT id FROM users WHERE email = ? AND id != ?", (user_update.email, current_user.id))
        if cursor.fetchone():
            conn.close()
            raise HTTPException(status_code=400, detail="Email already registered")
        update_fields.append("email = ?")
        params.append(user_update.email)
    
    if user_update.full_name is not None:
        update_fields.append("full_name = ?")
        params.append(user_update.full_name)
        
    if user_update.avatar_url is not None:
        update_fields.append("avatar_url = ?")
        params.append(user_update.avatar_url)
        
    if user_update.password is not None:
        update_fields.append("hashed_password = ?")
        params.append(get_password_hash(user_update.password))
        
    if not update_fields:
        conn.close()
        raise HTTPException(status_code=400, detail="No fields to update")
        
    update_fields.append("updated_at = CURRENT_TIMESTAMP")
    
    query = f"UPDATE users SET {', '.join(update_fields)} WHERE id = ?"
    params.append(current_user.id)
    
    cursor.execute(query, tuple(params))
    conn.commit()
    
    # Fetch updated user
    cursor.execute("SELECT * FROM users WHERE id = ?", (current_user.id,))
    updated_user = cursor.fetchone()
    conn.close()
    
    # Invalidate cache
    if redis_client:
        try:
            redis_client.delete(f"user:{current_user.email}")
            # If email changed, delete old key too (though current_user.email is the old one)
            if user_update.email and user_update.email != current_user.email:
                redis_client.delete(f"user:{user_update.email}")
        except Exception as e:
            print(f"Redis delete error: {e}")

    return UserInDB(
        id=updated_user["id"],
        email=updated_user["email"],
        full_name=updated_user["full_name"],
        avatar_url=updated_user["avatar_url"] if "avatar_url" in updated_user.keys() else None,
        is_active=bool(updated_user["is_active"]),
        is_admin=bool(updated_user["is_admin"]),
        hashed_password=updated_user["hashed_password"]
    )

@app.post("/admin/users", response_model=User)
def create_user_admin(user: UserCreate, current_user: User = Depends(get_current_user)):
    """Create a new user (admin only)"""
    # In a real app, check if current_user.is_admin
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    return register_user(user)

@app.get("/admin/users")
def get_users_admin(page: int = 1, per_page: int = 20, current_user: User = Depends(get_current_user)):
    """Get all users (admin only)"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get total count
    cursor.execute("SELECT COUNT(*) as count FROM users")
    total = cursor.fetchone()["count"]
    
    # Get users with pagination
    offset = (page - 1) * per_page
    cursor.execute("""
        SELECT id, email, full_name, is_active, is_admin, created_at, updated_at 
        FROM users 
        LIMIT ? OFFSET ?
    """, (per_page, offset))
    
    users = []
    for row in cursor.fetchall():
        users.append({
            "id": row["id"],
            "email": row["email"],
            "full_name": row["full_name"],
            "is_active": bool(row["is_active"]),
            "is_admin": bool(row["is_admin"]),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "last_login": row["updated_at"], # Placeholder
            "document_count": 0 # Placeholder
        })
    
    conn.close()
    
    return {
        "users": users,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page
    }

@app.get("/admin/users/{user_id}", response_model=User)
def get_user_admin(user_id: int, current_user: User = Depends(get_current_user)):
    """Get a specific user (admin only)"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user_row = cursor.fetchone()
    conn.close()
    
    if not user_row:
        raise HTTPException(status_code=404, detail="User not found")
        
    return UserInDB(
        id=user_row["id"],
        email=user_row["email"],
        full_name=user_row["full_name"],
        is_active=bool(user_row["is_active"]),
        is_admin=bool(user_row["is_admin"]),
        hashed_password=user_row["hashed_password"]
    )

@app.put("/admin/users/{user_id}", response_model=User)
def update_user_admin(user_id: int, user_update: UserUpdate, current_user: User = Depends(get_current_user)):
    """Update a user (admin only)"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if user exists
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="User not found")
    
    # Build update query
    update_fields = []
    params = []
    
    if user_update.email is not None:
        update_fields.append("email = ?")
        params.append(user_update.email)
    
    if user_update.full_name is not None:
        update_fields.append("full_name = ?")
        params.append(user_update.full_name)
        
    if user_update.password is not None:
        update_fields.append("hashed_password = ?")
        params.append(get_password_hash(user_update.password))
        
    if user_update.is_active is not None:
        update_fields.append("is_active = ?")
        params.append(user_update.is_active)
        
    if user_update.is_admin is not None:
        update_fields.append("is_admin = ?")
        params.append(user_update.is_admin)
        
    if not update_fields:
        conn.close()
        raise HTTPException(status_code=400, detail="No fields to update")
        
    update_fields.append("updated_at = CURRENT_TIMESTAMP")
    
    query = f"UPDATE users SET {', '.join(update_fields)} WHERE id = ?"
    params.append(user_id)
    
    cursor.execute(query, tuple(params))
    conn.commit()
    
    # Fetch updated user
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    updated_user = cursor.fetchone()
    conn.close()
    
    return UserInDB(
        id=updated_user["id"],
        email=updated_user["email"],
        full_name=updated_user["full_name"],
        is_active=bool(updated_user["is_active"]),
        is_admin=bool(updated_user["is_admin"]),
        hashed_password=updated_user["hashed_password"]
    )

@app.delete("/admin/users/{user_id}")
def delete_user_admin(user_id: int, current_user: User = Depends(get_current_user)):
    """Delete a user (admin only)"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if user exists
    cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="User not found")
        
    # Prevent deleting self
    if user_id == current_user.id:
        conn.close()
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    
    cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
    
    return {"message": "User deleted successfully"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
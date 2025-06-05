import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from minio import Minio

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Storage configuration
STORAGE_PATH = os.environ.get("STORAGE_PATH", "/data")

# Database configuration
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:////data/db/financial_analyst.db")

# MinIO configuration
MINIO_ENDPOINT = os.environ.get("MINIO_ENDPOINT", "minio:9000")
MINIO_ACCESS_KEY = os.environ.get("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.environ.get("MINIO_SECRET_KEY", "minioadmin")
MINIO_SECURE = os.environ.get("MINIO_SECURE", "false").lower() == "true"
DOCUMENTS_BUCKET = os.environ.get("DOCUMENTS_BUCKET", "documents")

def ensure_dir_exists(dir_path):
    """Ensure directory exists, create if it doesn't."""
    try:
        os.makedirs(dir_path, exist_ok=True)
        logger.info(f"Ensured directory exists: {dir_path}")
        return True
    except Exception as e:
        logger.error(f"Error creating directory {dir_path}: {e}")
        return False

def setup_directories():
    """Create necessary directories."""
    directories = [
        STORAGE_PATH,
        f"{STORAGE_PATH}/temp",
        f"{STORAGE_PATH}/db",
        f"{STORAGE_PATH}/vector_db",
        f"{STORAGE_PATH}/cache"
    ]
    
    for directory in directories:
        ensure_dir_exists(directory)

def setup_database():
    """Setup database connection and verify it's writable."""
    logger.info(f"Using database URL: {DATABASE_URL}")
    
    # Ensure database directory exists
    db_path = DATABASE_URL.replace("sqlite:///", "")
    db_dir = os.path.dirname(db_path)
    ensure_dir_exists(db_dir)
    
    # Verify database file is writable
    try:
        with open(db_path, 'a') as f:
            pass
        logger.info(f"Successfully verified database file is writable: {db_path}")
    except Exception as e:
        logger.error(f"Error verifying database file is writable: {e}")
    
    # Create SQLAlchemy engine with thread safety for SQLite
    engine = create_engine(
        DATABASE_URL, 
        connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    return engine, SessionLocal

def setup_minio():
    """Setup MinIO client and create bucket if needed."""
    try:
        minio_client = Minio(
            MINIO_ENDPOINT,
            access_key=MINIO_ACCESS_KEY,
            secret_key=MINIO_SECRET_KEY,
            secure=MINIO_SECURE
        )
        logger.info(f"MinIO client initialized with endpoint: {MINIO_ENDPOINT}")
        
        # Create bucket if it doesn't exist
        if not minio_client.bucket_exists(DOCUMENTS_BUCKET):
            minio_client.make_bucket(DOCUMENTS_BUCKET)
            logger.info(f"Created bucket: {DOCUMENTS_BUCKET}")
        else:
            logger.info(f"Bucket already exists: {DOCUMENTS_BUCKET}")
        
        return minio_client
    except Exception as e:
        logger.error(f"Error initializing MinIO client: {e}")
        return None

# Initialize components
setup_directories()
engine, SessionLocal = setup_database()
minio_client = setup_minio()
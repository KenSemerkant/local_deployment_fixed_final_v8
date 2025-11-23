#!/usr/bin/env python3
"""
Local version of the mock data population script that works without Docker.
This script creates a local SQLite database and populates it with mock analytics data.
"""

import os
import sys
import random
from datetime import datetime, timedelta
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Float, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext

# Create local data directory
LOCAL_DATA_DIR = os.path.join(os.path.dirname(__file__), "local_data")
os.makedirs(LOCAL_DATA_DIR, exist_ok=True)
os.makedirs(os.path.join(LOCAL_DATA_DIR, "db"), exist_ok=True)

# Local database configuration
DATABASE_URL = f"sqlite:///{LOCAL_DATA_DIR}/db/financial_analyst.db"

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Database setup
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    full_name = Column(String)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    original_filename = Column(String)
    file_size = Column(Integer)
    content_type = Column(String)
    upload_date = Column(DateTime, default=datetime.utcnow)
    user_id = Column(Integer, index=True)
    processing_status = Column(String, default="pending")
    analysis_result = Column(Text, nullable=True)

class AnalyticsEvent(Base):
    __tablename__ = "analytics_events"

    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String, index=True)
    user_id = Column(Integer, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    event_metadata = Column(Text, nullable=True)
    session_id = Column(String, nullable=True)
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)

class TokenUsage(Base):
    __tablename__ = "token_usage"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    document_id = Column(Integer, nullable=True)
    operation_type = Column(String)  # analysis, embedding, chat
    input_tokens = Column(Integer)
    output_tokens = Column(Integer)
    total_tokens = Column(Integer)
    cost = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)
    model_name = Column(String)

def create_mock_users(session, count=25):
    """Create mock users with realistic data."""
    first_names = [
        "Alice", "Bob", "Charlie", "Diana", "Edward", "Fiona", "George", "Hannah",
        "Ian", "Julia", "Kevin", "Laura", "Michael", "Nancy", "Oliver", "Patricia",
        "Quinn", "Rachel", "Samuel", "Teresa", "Ulrich", "Victoria", "William", "Xara",
        "Yuki", "Zachary", "Emma", "Liam", "Olivia", "Noah", "Ava", "Ethan", "Sophia"
    ]
    
    last_names = [
        "Anderson", "Brown", "Clark", "Davis", "Evans", "Fisher", "Garcia", "Harris",
        "Johnson", "King", "Lee", "Miller", "Nelson", "O'Connor", "Parker", "Quinn",
        "Rodriguez", "Smith", "Taylor", "Underwood", "Valdez", "Wilson", "Young", "Zhang"
    ]
    
    companies = ["TechCorp", "DataSys", "FinanceInc", "GlobalLtd", "InnovateGroup", "MarketLeaders"]
    
    users = []
    for i in range(count):
        first_name = random.choice(first_names)
        last_name = random.choice(last_names)
        company = random.choice(companies)
        
        email = f"{first_name.lower()}.{last_name.lower()}@{company.lower()}.com"
        full_name = f"{first_name} {last_name}"
        
        created_date = datetime.utcnow() - timedelta(days=random.randint(1, 365))
        last_login_date = None
        
        if random.random() < 0.8:  # 80% have logged in
            last_login_date = created_date + timedelta(days=random.randint(0, 30))
        
        user = User(
            email=email,
            hashed_password=pwd_context.hash("password123"),
            full_name=full_name,
            is_active=random.random() < 0.95,
            is_admin=i < 3,  # First 3 users are admins
            created_at=created_date,
            updated_at=created_date,
            last_login=last_login_date
        )
        
        session.add(user)
        users.append(user)
    
    session.commit()
    return users

def create_mock_documents(session, users, count=100):
    """Create mock documents."""
    document_types = [
        "financial_report.pdf", "quarterly_earnings.pdf", "market_analysis.pdf",
        "investment_strategy.pdf", "risk_assessment.pdf", "budget_forecast.pdf",
        "annual_report.pdf", "cash_flow_statement.pdf", "balance_sheet.pdf"
    ]
    
    statuses = ["completed", "processing", "failed", "pending"]
    
    documents = []
    for i in range(count):
        user = random.choice(users)
        filename = f"doc_{i}_{random.choice(document_types)}"
        
        upload_date = user.created_at + timedelta(days=random.randint(0, 30))
        
        doc = Document(
            filename=filename,
            original_filename=random.choice(document_types),
            file_size=random.randint(50000, 5000000),  # 50KB to 5MB
            content_type="application/pdf",
            upload_date=upload_date,
            user_id=user.id,
            processing_status=random.choice(statuses),
            analysis_result="Mock analysis result" if random.random() < 0.7 else None
        )
        
        session.add(doc)
        documents.append(doc)
    
    session.commit()
    return documents

def create_mock_analytics_events(session, users, count=500):
    """Create mock analytics events."""
    event_types = [
        "login", "logout", "document_upload", "document_view", "analysis_request",
        "dashboard_view", "settings_change", "search", "export", "share"
    ]
    
    events = []
    for i in range(count):
        user = random.choice(users)
        event_time = user.created_at + timedelta(
            days=random.randint(0, 30),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59)
        )
        
        event = AnalyticsEvent(
            event_type=random.choice(event_types),
            user_id=user.id,
            timestamp=event_time,
            event_metadata=f'{{"page": "dashboard", "action": "click"}}',
            session_id=f"session_{random.randint(1000, 9999)}",
            ip_address=f"192.168.1.{random.randint(1, 254)}",
            user_agent="Mozilla/5.0 (Mock Browser)"
        )
        
        session.add(event)
        events.append(event)
    
    session.commit()
    return events

def create_mock_token_usage(session, users, documents, count=200):
    """Create mock token usage data."""
    operations = ["analysis", "embedding", "chat", "summarization"]
    models = ["gpt-4", "gpt-3.5-turbo", "text-embedding-ada-002", "claude-3-sonnet"]
    
    usage_records = []
    for i in range(count):
        user = random.choice(users)
        document = random.choice(documents) if random.random() < 0.7 else None
        operation = random.choice(operations)
        model = random.choice(models)
        
        input_tokens = random.randint(100, 5000)
        output_tokens = random.randint(50, 2000)
        total_tokens = input_tokens + output_tokens
        
        # Mock cost calculation (rough estimates)
        cost_per_token = {
            "gpt-4": 0.00003,
            "gpt-3.5-turbo": 0.000002,
            "text-embedding-ada-002": 0.0000001,
            "claude-3-sonnet": 0.000015
        }
        cost = total_tokens * cost_per_token.get(model, 0.00001)
        
        timestamp = user.created_at + timedelta(
            days=random.randint(0, 30),
            hours=random.randint(0, 23)
        )
        
        usage = TokenUsage(
            user_id=user.id,
            document_id=document.id if document else None,
            operation_type=operation,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            cost=cost,
            timestamp=timestamp,
            model_name=model
        )
        
        session.add(usage)
        usage_records.append(usage)
    
    session.commit()
    return usage_records

def main():
    """Main function to populate mock analytics data."""
    print("🚀 Starting Local Mock Analytics Data Population")
    print("=" * 60)
    
    # Create database engine and session
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    
    try:
        print(f"📊 Database created at: {DATABASE_URL}")
        
        # Create mock data
        print("👥 Creating mock users...")
        users = create_mock_users(session, 25)
        print(f"✅ Created {len(users)} users")
        
        print("📄 Creating mock documents...")
        documents = create_mock_documents(session, users, 100)
        print(f"✅ Created {len(documents)} documents")
        
        print("📈 Creating mock analytics events...")
        events = create_mock_analytics_events(session, users, 500)
        print(f"✅ Created {len(events)} analytics events")
        
        print("🎯 Creating mock token usage data...")
        token_usage = create_mock_token_usage(session, users, documents, 200)
        print(f"✅ Created {len(token_usage)} token usage records")
        
        # Summary
        print("\n📊 Summary:")
        print(f"  - Users: {session.query(User).count()}")
        print(f"  - Documents: {session.query(Document).count()}")
        print(f"  - Analytics Events: {session.query(AnalyticsEvent).count()}")
        print(f"  - Token Usage Records: {session.query(TokenUsage).count()}")
        
        print(f"\n🔑 Default password for all demo users: password123")
        print(f"📁 Database location: {LOCAL_DATA_DIR}/db/financial_analyst.db")
        print(f"🌐 You can now access analytics data through the backend API")
        
    except Exception as e:
        print(f"❌ Error populating mock data: {e}")
        session.rollback()
        raise
    finally:
        session.close()

if __name__ == "__main__":
    main()

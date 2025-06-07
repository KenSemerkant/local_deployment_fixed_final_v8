"""
Script to populate the database with realistic mock analytics data
for demonstration purposes.
"""

import os
import sys
import random
import json
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

# Add the backend directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import SessionLocal
from models import (
    User, Document, Question, QASession, AnalysisResult,
    AnalyticsEvent, TokenUsage, PerformanceMetrics, UserFeedback
)

def create_mock_users(db: Session, count: int = 10):
    """Create mock users."""
    users = []
    for i in range(count):
        user = User(
            email=f"user{i+1}@example.com",
            full_name=f"User {i+1}",
            hashed_password="$2b$12$dummy_hash",
            is_active=True,
            is_admin=False,
            last_login=datetime.utcnow() - timedelta(days=random.randint(0, 30))
        )
        db.add(user)
        users.append(user)
    
    db.commit()
    return users

def create_mock_documents(db: Session, users: list, count: int = 50):
    """Create mock documents."""
    documents = []
    document_names = [
        "Q3_Financial_Report.pdf", "Annual_Budget_2024.xlsx", "Market_Analysis.docx",
        "Investment_Strategy.pdf", "Risk_Assessment.pdf", "Quarterly_Earnings.pdf",
        "Cash_Flow_Statement.xlsx", "Balance_Sheet.pdf", "Income_Statement.pdf",
        "Financial_Projections.xlsx", "Audit_Report.pdf", "Tax_Documents.pdf",
        "Merger_Analysis.docx", "Due_Diligence.pdf", "Compliance_Report.pdf"
    ]
    
    for i in range(count):
        user = random.choice(users)
        filename = random.choice(document_names)
        
        document = Document(
            filename=f"{i+1}_{filename}",
            file_path=f"/data/temp/{user.id}/{i+1}_{filename}",
            file_size=random.randint(100000, 10000000),  # 100KB to 10MB
            mime_type="application/pdf",
            owner_id=user.id,
            created_at=datetime.utcnow() - timedelta(days=random.randint(0, 90))
        )
        db.add(document)
        documents.append(document)
    
    db.commit()
    return documents

def create_mock_qa_sessions_and_questions(db: Session, documents: list, count: int = 200):
    """Create mock Q&A sessions and questions."""
    questions_list = [
        "What is the total revenue for this quarter?",
        "What are the main risk factors mentioned?",
        "How much did operating expenses increase?",
        "What is the profit margin?",
        "Are there any significant changes in cash flow?",
        "What are the key financial highlights?",
        "How does this compare to last year?",
        "What are the future growth projections?",
        "Are there any regulatory concerns?",
        "What is the debt-to-equity ratio?",
        "How is the company performing against competitors?",
        "What are the main cost drivers?",
        "Are there any one-time charges?",
        "What is the return on investment?",
        "How stable is the revenue stream?"
    ]
    
    answers_list = [
        "Based on the financial report, the total revenue for this quarter is $2.5 million, representing a 15% increase from the previous quarter.",
        "The main risk factors include market volatility, regulatory changes, and increased competition in the sector.",
        "Operating expenses increased by 8% compared to the previous period, primarily due to increased personnel costs and technology investments.",
        "The profit margin for this period is 12.5%, which is within the target range of 10-15%.",
        "Cash flow from operations shows a positive trend with $1.2 million generated this quarter.",
        "Key financial highlights include strong revenue growth, improved operational efficiency, and successful cost management initiatives.",
        "Compared to last year, the company shows 20% revenue growth and improved profitability metrics.",
        "Future growth projections indicate a 15-20% annual growth rate over the next three years.",
        "There are some regulatory concerns regarding new compliance requirements in the financial sector.",
        "The debt-to-equity ratio is 0.45, indicating a healthy balance between debt and equity financing."
    ]
    
    questions = []
    for i in range(count):
        document = random.choice(documents)
        
        # Create QA session
        qa_session = QASession(
            document_id=document.id,
            created_at=datetime.utcnow() - timedelta(days=random.randint(0, 60))
        )
        db.add(qa_session)
        db.flush()
        
        # Create 1-5 questions per session
        num_questions = random.randint(1, 5)
        for j in range(num_questions):
            question_text = random.choice(questions_list)
            answer_text = random.choice(answers_list)
            
            question = Question(
                question_text=question_text,
                answer_text=answer_text,
                sources=json.dumps([{"page": random.randint(1, 20), "content": "Sample source content"}]),
                session_id=qa_session.id,
                created_at=qa_session.created_at + timedelta(minutes=j*5)
            )
            db.add(question)
            questions.append(question)
    
    db.commit()
    return questions

def create_mock_analytics_events(db: Session, users: list, count: int = 1000):
    """Create mock analytics events."""
    event_types = [
        "LOGIN", "LOGOUT", "DOCUMENT_UPLOAD", "DOCUMENT_VIEW", "ANALYSIS_START",
        "ANALYSIS_COMPLETE", "QUESTION_ASK", "QUESTION_VIEW", "FEEDBACK_SUBMIT"
    ]
    
    for i in range(count):
        user = random.choice(users)
        event_type = random.choice(event_types)
        
        event_data = {}
        if event_type == "DOCUMENT_UPLOAD":
            event_data = {"filename": f"document_{i}.pdf", "file_size": random.randint(100000, 5000000)}
        elif event_type == "QUESTION_ASK":
            event_data = {"question_length": random.randint(20, 200), "answer_length": random.randint(100, 1000)}
        
        event = AnalyticsEvent(
            user_id=user.id,
            event_type=event_type,
            event_data=json.dumps(event_data),
            timestamp=datetime.utcnow() - timedelta(
                days=random.randint(0, 90),
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59)
            ),
            session_id=f"session_{random.randint(1000, 9999)}",
            ip_address=f"192.168.1.{random.randint(1, 254)}",
            user_agent="Mozilla/5.0 (Mock Browser)"
        )
        db.add(event)
    
    db.commit()

def create_mock_token_usage(db: Session, users: list, documents: list, questions: list, count: int = 500):
    """Create mock token usage data."""
    vendors = ["openai", "anthropic", "ollama", "lmstudio"]
    models = {
        "openai": ["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"],
        "anthropic": ["claude-3-opus", "claude-3-sonnet", "claude-3-haiku"],
        "ollama": ["llama2", "mistral", "codellama"],
        "lmstudio": ["deepseek-r1", "qwen", "phi"]
    }
    operations = ["ANALYSIS", "QUESTION", "EMBEDDING", "SUMMARY"]
    
    # Token cost estimates (USD per 1K tokens)
    token_costs = {
        "openai": {"gpt-4o": {"input": 0.005, "output": 0.015}},
        "anthropic": {"claude-3-sonnet": {"input": 0.003, "output": 0.015}},
        "ollama": {"llama2": {"input": 0.0, "output": 0.0}},
        "lmstudio": {"deepseek-r1": {"input": 0.0, "output": 0.0}}
    }
    
    for i in range(count):
        user = random.choice(users)
        vendor = random.choice(vendors)
        model = random.choice(models[vendor])
        operation = random.choice(operations)
        
        input_tokens = random.randint(100, 2000)
        output_tokens = random.randint(50, 1500)
        total_tokens = input_tokens + output_tokens
        
        # Calculate cost
        cost_info = token_costs.get(vendor, {}).get(model, {"input": 0.0, "output": 0.0})
        cost_estimate = (input_tokens / 1000 * cost_info["input"]) + (output_tokens / 1000 * cost_info["output"])
        
        token_usage = TokenUsage(
            user_id=user.id,
            document_id=random.choice(documents).id if random.random() > 0.3 else None,
            question_id=random.choice(questions).id if random.random() > 0.5 else None,
            operation_type=operation,
            model_name=model,
            vendor=vendor,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            cost_estimate=cost_estimate,
            timestamp=datetime.utcnow() - timedelta(
                days=random.randint(0, 90),
                hours=random.randint(0, 23)
            )
        )
        db.add(token_usage)
    
    db.commit()

def create_mock_performance_metrics(db: Session, users: list, documents: list, questions: list, count: int = 300):
    """Create mock performance metrics."""
    operations = ["DOCUMENT_ANALYSIS", "EMBEDDING_CREATION", "QUESTION_ANSWERING", "DOCUMENT_UPLOAD"]
    
    for i in range(count):
        user = random.choice(users)
        operation = random.choice(operations)
        
        # Different duration ranges for different operations
        if operation == "DOCUMENT_ANALYSIS":
            duration = random.uniform(10.0, 120.0)  # 10s to 2 minutes
        elif operation == "EMBEDDING_CREATION":
            duration = random.uniform(5.0, 60.0)   # 5s to 1 minute
        elif operation == "QUESTION_ANSWERING":
            duration = random.uniform(2.0, 30.0)   # 2s to 30s
        else:  # DOCUMENT_UPLOAD
            duration = random.uniform(1.0, 15.0)   # 1s to 15s
        
        start_time = datetime.utcnow() - timedelta(
            days=random.randint(0, 90),
            hours=random.randint(0, 23)
        )
        end_time = start_time + timedelta(seconds=duration)
        
        success = random.random() > 0.05  # 95% success rate
        
        metric = PerformanceMetrics(
            user_id=user.id,
            document_id=random.choice(documents).id if operation in ["DOCUMENT_ANALYSIS", "DOCUMENT_UPLOAD"] else None,
            question_id=random.choice(questions).id if operation == "QUESTION_ANSWERING" else None,
            operation_type=operation,
            start_time=start_time,
            end_time=end_time,
            duration_seconds=duration,
            file_size_bytes=random.randint(100000, 10000000) if operation in ["DOCUMENT_ANALYSIS", "DOCUMENT_UPLOAD"] else None,
            success=success,
            error_message="Network timeout" if not success else None
        )
        db.add(metric)
    
    db.commit()

def create_mock_user_feedback(db: Session, users: list, questions: list, documents: list, count: int = 150):
    """Create mock user feedback."""
    feedback_types = ["RATING", "THUMBS_UP", "THUMBS_DOWN", "COMMENT"]
    comments = [
        "Very helpful analysis, exactly what I needed!",
        "The response was accurate and well-structured.",
        "Could be more detailed in the financial projections section.",
        "Great insights into the risk factors.",
        "The analysis helped me understand the cash flow better.",
        "Response time was fast and the answer was comprehensive.",
        "Would like to see more comparative analysis.",
        "Excellent breakdown of the financial metrics.",
        "The source citations were very useful.",
        "Clear and concise explanation of complex financial data."
    ]
    
    for i in range(count):
        user = random.choice(users)
        feedback_type = random.choice(feedback_types)
        
        rating = None
        comment = None
        helpful = None
        
        if feedback_type == "RATING":
            rating = random.randint(3, 5)  # Mostly positive ratings
        elif feedback_type == "THUMBS_UP":
            helpful = True
        elif feedback_type == "THUMBS_DOWN":
            helpful = False
        elif feedback_type == "COMMENT":
            comment = random.choice(comments)
            rating = random.randint(3, 5)
        
        feedback = UserFeedback(
            user_id=user.id,
            question_id=random.choice(questions).id if random.random() > 0.3 else None,
            document_id=random.choice(documents).id if random.random() > 0.7 else None,
            feedback_type=feedback_type,
            rating=rating,
            comment=comment,
            helpful=helpful,
            timestamp=datetime.utcnow() - timedelta(
                days=random.randint(0, 60),
                hours=random.randint(0, 23)
            )
        )
        db.add(feedback)
    
    db.commit()

def main():
    """Main function to populate all mock data."""
    print("Starting to populate mock analytics data...")
    
    # Get database session
    db = SessionLocal()
    
    try:
        # Create mock data
        print("Creating mock users...")
        users = create_mock_users(db, 15)
        
        print("Creating mock documents...")
        documents = create_mock_documents(db, users, 75)
        
        print("Creating mock Q&A sessions and questions...")
        questions = create_mock_qa_sessions_and_questions(db, documents, 300)
        
        print("Creating mock analytics events...")
        create_mock_analytics_events(db, users, 1500)
        
        print("Creating mock token usage data...")
        create_mock_token_usage(db, users, documents, questions, 800)
        
        print("Creating mock performance metrics...")
        create_mock_performance_metrics(db, users, documents, questions, 500)
        
        print("Creating mock user feedback...")
        create_mock_user_feedback(db, users, questions, documents, 200)
        
        print("✅ Mock data population completed successfully!")
        print(f"Created:")
        print(f"  - {len(users)} users")
        print(f"  - {len(documents)} documents")
        print(f"  - {len(questions)} questions")
        print(f"  - 1500 analytics events")
        print(f"  - 800 token usage records")
        print(f"  - 500 performance metrics")
        print(f"  - 200 user feedback entries")
        
    except Exception as e:
        print(f"❌ Error populating mock data: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main()

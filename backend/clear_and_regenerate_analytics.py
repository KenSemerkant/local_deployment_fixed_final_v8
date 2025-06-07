"""
Script to clear existing analytics data and regenerate realistic data
for the past 2 months based on actual users in the system.
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

def clear_analytics_data(db: Session):
    """Clear all analytics and related data, keeping only users."""
    print("Clearing existing analytics data...")
    
    # Delete in reverse dependency order
    db.query(UserFeedback).delete()
    db.query(PerformanceMetrics).delete()
    db.query(TokenUsage).delete()
    db.query(AnalyticsEvent).delete()
    db.query(Question).delete()
    db.query(QASession).delete()
    db.query(AnalysisResult).delete()
    db.query(Document).delete()
    
    db.commit()
    print("✅ Analytics data cleared successfully")

def get_actual_users(db: Session):
    """Get all actual users from the system."""
    users = db.query(User).all()
    print(f"Found {len(users)} users in the system")
    return users

def create_realistic_documents(db: Session, users: list, start_date: datetime):
    """Create realistic documents for the past 2 months."""
    documents = []
    
    # Realistic financial document names
    document_templates = [
        "Q{quarter}_Financial_Report_{year}.pdf",
        "Monthly_Budget_{month}_{year}.xlsx", 
        "Market_Analysis_{month}_{year}.docx",
        "Investment_Portfolio_{month}_{year}.pdf",
        "Risk_Assessment_{month}_{year}.pdf",
        "Quarterly_Earnings_Q{quarter}_{year}.pdf",
        "Cash_Flow_Statement_{month}_{year}.xlsx",
        "Balance_Sheet_{month}_{year}.pdf",
        "Income_Statement_{month}_{year}.pdf",
        "Financial_Projections_{year}.xlsx",
        "Audit_Report_{month}_{year}.pdf",
        "Tax_Documents_{year}.pdf",
        "Merger_Analysis_{company}.docx",
        "Due_Diligence_{company}.pdf",
        "Compliance_Report_{month}_{year}.pdf",
        "Annual_Report_{year}.pdf",
        "Budget_Variance_{month}_{year}.xlsx",
        "KPI_Dashboard_{month}_{year}.pdf"
    ]
    
    companies = ["TechCorp", "FinanceInc", "GlobalLtd", "InnovateGroup", "MarketLeaders"]
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    
    # Generate 3-8 documents per user over 2 months
    for user in users:
        num_docs = random.randint(3, 8)
        
        for i in range(num_docs):
            # Random date within the past 2 months
            days_ago = random.randint(0, 60)
            created_date = start_date + timedelta(days=days_ago)
            
            # Select and format document name
            template = random.choice(document_templates)
            quarter = random.randint(1, 4)
            year = created_date.year
            month = months[created_date.month - 1]
            company = random.choice(companies)
            
            filename = template.format(
                quarter=quarter, 
                year=year, 
                month=month, 
                company=company
            )
            
            document = Document(
                filename=filename,
                file_path=f"/data/temp/{user.id}/{filename}",
                file_size=random.randint(500000, 15000000),  # 500KB to 15MB
                mime_type=random.choice(["application/pdf", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]),
                owner_id=user.id,
                created_at=created_date
            )
            db.add(document)
            documents.append(document)
    
    db.commit()
    print(f"✅ Created {len(documents)} realistic documents")
    return documents

def create_realistic_qa_sessions(db: Session, documents: list, start_date: datetime):
    """Create realistic Q&A sessions and questions."""
    questions = []
    
    # More sophisticated financial questions
    financial_questions = [
        "What is the total revenue for this quarter and how does it compare to last quarter?",
        "What are the main risk factors mentioned in this report?",
        "How much did operating expenses increase year-over-year?",
        "What is the current profit margin and is it within target range?",
        "Are there any significant changes in cash flow from operations?",
        "What are the key financial highlights and lowlights?",
        "How does our performance compare to industry benchmarks?",
        "What are the future growth projections and assumptions?",
        "Are there any regulatory concerns or compliance issues?",
        "What is the current debt-to-equity ratio and debt service coverage?",
        "How is the company performing against budget and forecast?",
        "What are the main cost drivers and expense categories?",
        "Are there any one-time charges or extraordinary items?",
        "What is the return on investment for major initiatives?",
        "How stable and predictable is the revenue stream?",
        "What are the working capital requirements and trends?",
        "How effective is our capital allocation strategy?",
        "What are the key performance indicators and metrics?",
        "Are there any material weaknesses in internal controls?",
        "What is the outlook for the next quarter and fiscal year?"
    ]
    
    # Realistic answers with financial context
    financial_answers = [
        "Based on the financial report, total revenue for this quarter is $2.8 million, representing a 12% increase from the previous quarter of $2.5 million. This growth is primarily driven by increased sales in our core product lines and successful market expansion initiatives.",
        "The main risk factors include market volatility (15% impact), regulatory changes in financial services (10% impact), increased competition from fintech startups (20% impact), and potential supply chain disruptions (8% impact).",
        "Operating expenses increased by 8.5% year-over-year, from $1.2 million to $1.3 million. The increase is primarily due to strategic investments in technology infrastructure ($75K), increased personnel costs ($45K), and higher marketing spend ($30K).",
        "The current profit margin is 14.2%, which is above our target range of 12-15%. This represents an improvement from last quarter's 13.1% and demonstrates effective cost management and operational efficiency improvements.",
        "Cash flow from operations shows a positive trend with $1.4 million generated this quarter, compared to $1.1 million last quarter. This 27% improvement reflects better collection processes and optimized working capital management.",
        "Key financial highlights include: 12% revenue growth, improved profit margins, strong cash generation, and successful cost optimization. Areas of concern include increased customer acquisition costs and higher than expected technology expenses.",
        "Our performance compares favorably to industry benchmarks. Our revenue growth of 12% exceeds the industry average of 8%, and our profit margin of 14.2% is above the sector median of 11.5%.",
        "Future growth projections indicate 15-18% annual revenue growth over the next three years, based on market expansion, new product launches, and strategic partnerships. Key assumptions include stable market conditions and successful execution of our growth strategy.",
        "There are emerging regulatory concerns regarding new data privacy requirements and potential changes to financial reporting standards. We are actively monitoring these developments and have allocated $200K for compliance initiatives.",
        "The current debt-to-equity ratio is 0.42, indicating a conservative capital structure. Our debt service coverage ratio of 3.2x demonstrates strong ability to meet debt obligations and provides flexibility for future investments."
    ]
    
    # Create Q&A sessions for documents (60% of documents get questions)
    for document in documents:
        if random.random() < 0.6:  # 60% chance of having Q&A
            # Create QA session
            session_date = document.created_at + timedelta(
                hours=random.randint(1, 72)  # Questions asked 1-72 hours after upload
            )
            
            qa_session = QASession(
                document_id=document.id,
                created_at=session_date
            )
            db.add(qa_session)
            db.flush()
            
            # Create 1-4 questions per session
            num_questions = random.randint(1, 4)
            for j in range(num_questions):
                question_text = random.choice(financial_questions)
                answer_text = random.choice(financial_answers)
                
                question = Question(
                    question_text=question_text,
                    answer_text=answer_text,
                    sources=json.dumps([{
                        "page": random.randint(1, 25), 
                        "content": f"Source content from page {random.randint(1, 25)} of {document.filename}",
                        "relevance_score": round(random.uniform(0.7, 0.95), 2)
                    }]),
                    session_id=qa_session.id,
                    created_at=session_date + timedelta(minutes=j*3)
                )
                db.add(question)
                questions.append(question)
    
    db.commit()
    print(f"✅ Created {len(questions)} realistic questions")
    return questions

def create_realistic_analytics_events(db: Session, users: list, documents: list, questions: list, start_date: datetime):
    """Create realistic analytics events based on user behavior patterns."""
    events = []
    
    event_types = [
        "LOGIN", "LOGOUT", "DOCUMENT_UPLOAD", "DOCUMENT_VIEW", "ANALYSIS_START",
        "ANALYSIS_COMPLETE", "QUESTION_ASK", "QUESTION_VIEW", "FEEDBACK_SUBMIT",
        "ADMIN_ACCESS", "SETTINGS_UPDATE", "SEARCH_PERFORM"
    ]
    
    # Create events for each day over the past 2 months
    current_date = start_date
    end_date = datetime.utcnow()
    
    while current_date <= end_date:
        # Simulate daily activity patterns
        is_weekday = current_date.weekday() < 5  # Monday = 0, Sunday = 6
        is_business_hours = 9 <= current_date.hour <= 17
        
        # More activity on weekdays and business hours
        activity_multiplier = 1.0
        if is_weekday:
            activity_multiplier *= 1.5
        if is_business_hours:
            activity_multiplier *= 2.0
        
        # Each user has a chance of being active each day
        for user in users:
            # Different users have different activity levels
            if user.is_admin:
                base_activity_chance = 0.8  # Admins more active
            else:
                base_activity_chance = 0.4  # Regular users less active
            
            daily_activity_chance = base_activity_chance * activity_multiplier
            
            if random.random() < daily_activity_chance:
                # User is active today, generate 1-8 events
                num_events = random.randint(1, 8)
                
                for _ in range(num_events):
                    event_type = random.choice(event_types)
                    
                    # Create realistic event timing within the day
                    event_time = current_date.replace(
                        hour=random.randint(8, 18),
                        minute=random.randint(0, 59),
                        second=random.randint(0, 59)
                    )
                    
                    event_data = {}
                    if event_type == "DOCUMENT_UPLOAD":
                        event_data = {
                            "filename": random.choice(documents).filename if documents else "sample.pdf",
                            "file_size": random.randint(500000, 10000000)
                        }
                    elif event_type == "QUESTION_ASK":
                        event_data = {
                            "question_length": random.randint(50, 300),
                            "answer_length": random.randint(200, 1500),
                            "processing_time": random.uniform(5.0, 45.0)
                        }
                    elif event_type == "ANALYSIS_START":
                        event_data = {
                            "document_id": random.choice(documents).id if documents else None,
                            "analysis_type": random.choice(["full", "summary", "key_metrics"])
                        }
                    
                    event = AnalyticsEvent(
                        user_id=user.id,
                        event_type=event_type,
                        event_data=json.dumps(event_data),
                        timestamp=event_time,
                        session_id=f"session_{random.randint(10000, 99999)}",
                        ip_address=f"192.168.{random.randint(1, 10)}.{random.randint(1, 254)}",
                        user_agent="Mozilla/5.0 (Analytics Mock Data)"
                    )
                    db.add(event)
                    events.append(event)
        
        current_date += timedelta(days=1)
    
    db.commit()
    print(f"✅ Created {len(events)} realistic analytics events")
    return events

def create_realistic_token_usage(db: Session, users: list, documents: list, questions: list, start_date: datetime):
    """Create realistic token usage data based on actual operations."""
    token_records = []

    vendors = ["openai", "anthropic", "ollama", "lmstudio"]
    models = {
        "openai": ["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"],
        "anthropic": ["claude-3-opus", "claude-3-sonnet", "claude-3-haiku"],
        "ollama": ["llama2", "mistral", "codellama"],
        "lmstudio": ["deepseek-r1", "qwen", "phi"]
    }
    operations = ["ANALYSIS", "QUESTION", "EMBEDDING", "SUMMARY"]

    # Realistic token costs (USD per 1K tokens)
    token_costs = {
        "openai": {
            "gpt-4o": {"input": 0.005, "output": 0.015},
            "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
            "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015}
        },
        "anthropic": {
            "claude-3-opus": {"input": 0.015, "output": 0.075},
            "claude-3-sonnet": {"input": 0.003, "output": 0.015},
            "claude-3-haiku": {"input": 0.00025, "output": 0.00125}
        },
        "ollama": {
            "llama2": {"input": 0.0, "output": 0.0},
            "mistral": {"input": 0.0, "output": 0.0},
            "codellama": {"input": 0.0, "output": 0.0}
        },
        "lmstudio": {
            "deepseek-r1": {"input": 0.0, "output": 0.0},
            "qwen": {"input": 0.0, "output": 0.0},
            "phi": {"input": 0.0, "output": 0.0}
        }
    }

    # Create token usage for each question and document analysis
    for question in questions:
        vendor = random.choice(vendors)
        model = random.choice(models[vendor])

        # Realistic token counts for Q&A
        input_tokens = random.randint(800, 3000)  # Question + context
        output_tokens = random.randint(300, 1200)  # Answer
        total_tokens = input_tokens + output_tokens

        cost_info = token_costs[vendor][model]
        cost_estimate = (input_tokens / 1000 * cost_info["input"]) + (output_tokens / 1000 * cost_info["output"])

        token_usage = TokenUsage(
            user_id=question.session.document.owner_id,
            document_id=question.session.document_id,
            question_id=question.id,
            operation_type="QUESTION",
            model_name=model,
            vendor=vendor,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            cost_estimate=cost_estimate,
            timestamp=question.created_at
        )
        db.add(token_usage)
        token_records.append(token_usage)

    # Create token usage for document analysis
    for document in documents:
        # Each document gets 1-2 analysis operations
        num_analyses = random.randint(1, 2)

        for _ in range(num_analyses):
            vendor = random.choice(vendors)
            model = random.choice(models[vendor])
            operation = random.choice(["ANALYSIS", "EMBEDDING", "SUMMARY"])

            # Different token patterns for different operations
            if operation == "ANALYSIS":
                input_tokens = random.randint(2000, 8000)  # Full document
                output_tokens = random.randint(800, 2500)  # Detailed analysis
            elif operation == "EMBEDDING":
                input_tokens = random.randint(1000, 4000)  # Document chunks
                output_tokens = 0  # Embeddings don't generate text
            else:  # SUMMARY
                input_tokens = random.randint(1500, 5000)  # Document content
                output_tokens = random.randint(200, 800)   # Summary

            total_tokens = input_tokens + output_tokens

            cost_info = token_costs[vendor][model]
            cost_estimate = (input_tokens / 1000 * cost_info["input"]) + (output_tokens / 1000 * cost_info["output"])

            # Analysis happens shortly after document upload
            analysis_time = document.created_at + timedelta(
                minutes=random.randint(5, 120)
            )

            token_usage = TokenUsage(
                user_id=document.owner_id,
                document_id=document.id,
                question_id=None,
                operation_type=operation,
                model_name=model,
                vendor=vendor,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=total_tokens,
                cost_estimate=cost_estimate,
                timestamp=analysis_time
            )
            db.add(token_usage)
            token_records.append(token_usage)

    db.commit()
    print(f"✅ Created {len(token_records)} realistic token usage records")
    return token_records

def create_realistic_performance_metrics(db: Session, users: list, documents: list, questions: list, start_date: datetime):
    """Create realistic performance metrics."""
    metrics = []

    operations = ["DOCUMENT_ANALYSIS", "EMBEDDING_CREATION", "QUESTION_ANSWERING", "DOCUMENT_UPLOAD"]

    # Performance metrics for document operations
    for document in documents:
        # Document upload performance
        upload_duration = random.uniform(2.0, 20.0)  # 2s to 20s based on file size
        if document.file_size > 5000000:  # Files > 5MB take longer
            upload_duration *= random.uniform(1.5, 3.0)

        upload_metric = PerformanceMetrics(
            user_id=document.owner_id,
            document_id=document.id,
            question_id=None,
            operation_type="DOCUMENT_UPLOAD",
            start_time=document.created_at - timedelta(seconds=upload_duration),
            end_time=document.created_at,
            duration_seconds=upload_duration,
            file_size_bytes=document.file_size,
            success=random.random() > 0.02,  # 98% success rate
            error_message="Network timeout" if random.random() < 0.02 else None
        )
        db.add(upload_metric)
        metrics.append(upload_metric)

        # Document analysis performance
        analysis_duration = random.uniform(15.0, 180.0)  # 15s to 3 minutes
        if document.file_size > 5000000:
            analysis_duration *= random.uniform(1.2, 2.0)

        analysis_start = document.created_at + timedelta(minutes=random.randint(1, 30))
        analysis_metric = PerformanceMetrics(
            user_id=document.owner_id,
            document_id=document.id,
            question_id=None,
            operation_type="DOCUMENT_ANALYSIS",
            start_time=analysis_start,
            end_time=analysis_start + timedelta(seconds=analysis_duration),
            duration_seconds=analysis_duration,
            file_size_bytes=document.file_size,
            success=random.random() > 0.05,  # 95% success rate
            error_message="Processing timeout" if random.random() < 0.05 else None
        )
        db.add(analysis_metric)
        metrics.append(analysis_metric)

        # Embedding creation performance
        embedding_duration = random.uniform(8.0, 90.0)  # 8s to 1.5 minutes
        embedding_start = analysis_start + timedelta(seconds=analysis_duration + random.randint(10, 60))

        embedding_metric = PerformanceMetrics(
            user_id=document.owner_id,
            document_id=document.id,
            question_id=None,
            operation_type="EMBEDDING_CREATION",
            start_time=embedding_start,
            end_time=embedding_start + timedelta(seconds=embedding_duration),
            duration_seconds=embedding_duration,
            file_size_bytes=document.file_size,
            success=random.random() > 0.03,  # 97% success rate
            error_message="Vector store error" if random.random() < 0.03 else None
        )
        db.add(embedding_metric)
        metrics.append(embedding_metric)

    # Performance metrics for questions
    for question in questions:
        qa_duration = random.uniform(3.0, 45.0)  # 3s to 45s

        qa_start = question.created_at
        qa_metric = PerformanceMetrics(
            user_id=question.session.document.owner_id,
            document_id=question.session.document_id,
            question_id=question.id,
            operation_type="QUESTION_ANSWERING",
            start_time=qa_start,
            end_time=qa_start + timedelta(seconds=qa_duration),
            duration_seconds=qa_duration,
            file_size_bytes=None,
            success=random.random() > 0.02,  # 98% success rate
            error_message="LLM timeout" if random.random() < 0.02 else None
        )
        db.add(qa_metric)
        metrics.append(qa_metric)

    db.commit()
    print(f"✅ Created {len(metrics)} realistic performance metrics")
    return metrics

def create_realistic_user_feedback(db: Session, users: list, questions: list, documents: list, start_date: datetime):
    """Create realistic user feedback."""
    feedback_records = []

    feedback_types = ["RATING", "THUMBS_UP", "THUMBS_DOWN", "COMMENT"]

    # Realistic feedback comments
    positive_comments = [
        "Excellent analysis! Very detailed and accurate insights.",
        "The response was exactly what I needed for my financial review.",
        "Great breakdown of the key metrics and trends.",
        "Very helpful in understanding the cash flow patterns.",
        "The analysis helped me identify important risk factors.",
        "Clear and comprehensive explanation of the financial data.",
        "Perfect for preparing my board presentation.",
        "The insights were spot-on and actionable.",
        "Saved me hours of manual analysis work.",
        "Outstanding quality and depth of analysis."
    ]

    neutral_comments = [
        "Good analysis overall, could use more detail on projections.",
        "Helpful but would like to see more comparative data.",
        "The response was accurate but took longer than expected.",
        "Useful information, though some sections could be clearer.",
        "Good starting point for further analysis."
    ]

    negative_comments = [
        "The analysis missed some key financial indicators.",
        "Response was too generic, needed more specific insights.",
        "Some of the calculations seem incorrect.",
        "Could be more detailed in the risk assessment section.",
        "The analysis didn't address my specific question fully."
    ]

    # Create feedback for 40% of questions (realistic feedback rate)
    for question in questions:
        if random.random() < 0.4:  # 40% feedback rate
            feedback_type = random.choice(feedback_types)

            # Bias toward positive feedback (realistic for good system)
            rating_bias = random.random()
            if rating_bias < 0.7:  # 70% positive
                rating = random.randint(4, 5)
                helpful = True
                comment = random.choice(positive_comments) if feedback_type == "COMMENT" else None
            elif rating_bias < 0.9:  # 20% neutral
                rating = 3
                helpful = random.choice([True, False])
                comment = random.choice(neutral_comments) if feedback_type == "COMMENT" else None
            else:  # 10% negative
                rating = random.randint(1, 2)
                helpful = False
                comment = random.choice(negative_comments) if feedback_type == "COMMENT" else None

            # Feedback comes 1-24 hours after question
            feedback_time = question.created_at + timedelta(
                hours=random.randint(1, 24)
            )

            feedback = UserFeedback(
                user_id=question.session.document.owner_id,
                question_id=question.id,
                document_id=question.session.document_id,
                feedback_type=feedback_type,
                rating=rating if feedback_type in ["RATING", "COMMENT"] else None,
                comment=comment,
                helpful=helpful if feedback_type in ["THUMBS_UP", "THUMBS_DOWN"] else None,
                timestamp=feedback_time
            )
            db.add(feedback)
            feedback_records.append(feedback)

    # Create some document-level feedback (10% of documents)
    for document in documents:
        if random.random() < 0.1:  # 10% document feedback rate
            rating = random.randint(3, 5)  # Generally positive for document analysis

            feedback_time = document.created_at + timedelta(
                hours=random.randint(2, 48)
            )

            feedback = UserFeedback(
                user_id=document.owner_id,
                question_id=None,
                document_id=document.id,
                feedback_type="RATING",
                rating=rating,
                comment=random.choice(positive_comments + neutral_comments),
                helpful=None,
                timestamp=feedback_time
            )
            db.add(feedback)
            feedback_records.append(feedback)

    db.commit()
    print(f"✅ Created {len(feedback_records)} realistic feedback records")
    return feedback_records

def main():
    """Main function to clear and regenerate analytics data."""
    print("🔄 Starting analytics data regeneration for past 2 months...")

    # Calculate start date (2 months ago)
    start_date = datetime.utcnow() - timedelta(days=60)

    # Get database session
    db = SessionLocal()

    try:
        # Clear existing analytics data
        clear_analytics_data(db)

        # Get actual users from the system
        users = get_actual_users(db)

        # Generate realistic data for past 2 months
        print(f"📅 Generating data from {start_date.strftime('%Y-%m-%d')} to {datetime.utcnow().strftime('%Y-%m-%d')}")

        print("📄 Creating realistic documents...")
        documents = create_realistic_documents(db, users, start_date)

        print("❓ Creating realistic Q&A sessions...")
        questions = create_realistic_qa_sessions(db, documents, start_date)

        print("📊 Creating realistic analytics events...")
        events = create_realistic_analytics_events(db, users, documents, questions, start_date)

        print("🎯 Creating realistic token usage...")
        token_records = create_realistic_token_usage(db, users, documents, questions, start_date)

        print("⚡ Creating realistic performance metrics...")
        metrics = create_realistic_performance_metrics(db, users, documents, questions, start_date)

        print("💬 Creating realistic user feedback...")
        feedback_records = create_realistic_user_feedback(db, users, questions, documents, start_date)

        print("\n🎉 Analytics data regeneration completed successfully!")
        print(f"📊 Summary:")
        print(f"  - {len(users)} users (existing)")
        print(f"  - {len(documents)} documents")
        print(f"  - {len(questions)} questions")
        print(f"  - {len(events)} analytics events")
        print(f"  - {len(token_records)} token usage records")
        print(f"  - {len(metrics)} performance metrics")
        print(f"  - {len(feedback_records)} feedback records")
        print(f"📅 Data covers: {start_date.strftime('%Y-%m-%d')} to {datetime.utcnow().strftime('%Y-%m-%d')}")

    except Exception as e:
        print(f"❌ Error regenerating analytics data: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    main()

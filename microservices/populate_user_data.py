#!/usr/bin/env python3
"""
Script to populate the user-service database with mock user data
for demonstration purposes.
"""

import os
import sys
import random
from datetime import datetime, timedelta
from passlib.context import CryptContext

# Add the user-service directory to the path
sys.path.append('/app')

from infrastructure.database import SessionLocal, UserModel

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_mock_users(db, count: int = 20):
    """Create mock users with realistic data."""
    
    # Sample data for generating realistic users
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
    existing_emails = set()
    
    # Get existing emails to avoid duplicates
    existing_users = db.query(UserModel.email).all()
    for user in existing_users:
        existing_emails.add(user.email)
    
    for i in range(count):
        first_name = random.choice(first_names)
        last_name = random.choice(last_names)
        company = random.choice(companies)
        
        # Generate email variations
        email_formats = [
            f"{first_name.lower()}.{last_name.lower()}@{company.lower()}.com",
            f"{first_name.lower()}{last_name.lower()}@{company.lower()}.com",
            f"{first_name[0].lower()}{last_name.lower()}@{company.lower()}.com",
            f"{first_name.lower()}.{last_name.lower()}{random.randint(1, 99)}@{company.lower()}.com"
        ]
        
        # Find a unique email
        email = None
        for email_format in email_formats:
            if email_format not in existing_emails:
                email = email_format
                existing_emails.add(email)
                break
        
        if not email:
            # Fallback with timestamp
            email = f"{first_name.lower()}.{last_name.lower()}.{int(datetime.utcnow().timestamp())}@{company.lower()}.com"
            existing_emails.add(email)
        
        full_name = f"{first_name} {last_name}"
        
        # Create user with realistic timestamps
        created_date = datetime.utcnow() - timedelta(days=random.randint(1, 365))
        last_login_date = None
        
        # 80% of users have logged in at least once
        if random.random() < 0.8:
            last_login_date = created_date + timedelta(days=random.randint(0, 30))
        
        # 10% chance of being admin (excluding the first few which should be regular users)
        is_admin = i > 5 and random.random() < 0.1
        
        user = UserModel(
            email=email,
            hashed_password=pwd_context.hash("password123"),  # Default password for demo
            full_name=full_name,
            is_active=random.random() < 0.95,  # 95% active users
            is_admin=is_admin,
            created_at=created_date,
            updated_at=created_date,
            last_login=last_login_date
        )
        
        db.add(user)
        users.append(user)
    
    db.commit()
    return users


def main():
    """Main function to populate mock data."""
    print("🚀 Starting User Service Mock Data Population")
    print("=" * 50)
    
    db = SessionLocal()
    
    try:
        # Check existing users
        existing_count = db.query(UserModel).count()
        print(f"📊 Current users in database: {existing_count}")
        
        if existing_count >= 20:
            print("✅ Database already has sufficient user data")
            print("🔄 Skipping user creation (20+ users already exist)")
            return
        
        # Create additional users to reach at least 20
        users_to_create = max(0, 20 - existing_count)
        
        if users_to_create > 0:
            print(f"👥 Creating {users_to_create} additional users...")
            users = create_mock_users(db, users_to_create)
            
            print("✅ User data population completed successfully!")
            print(f"📊 Summary:")
            print(f"  - Created: {len(users)} new users")
            print(f"  - Total users: {db.query(UserModel).count()}")
            print(f"  - Active users: {db.query(UserModel).filter(UserModel.is_active == True).count()}")
            print(f"  - Admin users: {db.query(UserModel).filter(UserModel.is_admin == True).count()}")
        
        # Display some sample users
        print("\n📋 Sample Users:")
        sample_users = db.query(UserModel).limit(5).all()
        for user in sample_users:
            status = "🟢 Active" if user.is_active else "🔴 Inactive"
            admin = " (Admin)" if user.is_admin else ""
            print(f"  - {user.full_name} ({user.email}) {status}{admin}")
        
        print(f"\n🔑 Default password for all demo users: password123")
        print(f"🌐 Access the application at: http://localhost:3000")
        
    except Exception as e:
        print(f"❌ Error populating user data: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()

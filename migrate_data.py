import sqlite3
import psycopg2
from psycopg2.extras import RealDictCursor
import json
import os
import sys

# Configuration
SQLITE_DB_PATH = "backend/local_data/db/financial_analyst.db"
POSTGRES_DSN = "host=localhost port=5432 dbname=app_db user=postgres password=postgres"

def get_sqlite_conn():
    if not os.path.exists(SQLITE_DB_PATH):
        print(f"Error: SQLite DB not found at {SQLITE_DB_PATH}")
        sys.exit(1)
    conn = sqlite3.connect(SQLITE_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_postgres_conn():
    try:
        conn = psycopg2.connect(POSTGRES_DSN)
        return conn
    except Exception as e:
        print(f"Error connecting to Postgres: {e}")
        sys.exit(1)

def migrate_users(sqlite_conn, pg_conn):
    print("Migrating users...")
    sqlite_cursor = sqlite_conn.cursor()
    pg_cursor = pg_conn.cursor()
    
    sqlite_cursor.execute("SELECT * FROM users")
    users = sqlite_cursor.fetchall()
    
    count = 0
    for user in users:
        try:
            pg_cursor.execute("""
                INSERT INTO users (id, email, hashed_password, full_name, is_active, is_admin, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
            """, (
                user['id'],
                user['email'],
                user['hashed_password'],
                user['full_name'],
                bool(user['is_active']),
                bool(user['is_admin']),
                user['created_at'],
                user['updated_at']
            ))
            count += 1
        except Exception as e:
            print(f"Error migrating user {user['id']}: {e}")
            
    pg_conn.commit()
    print(f"Migrated {count} users.")

def migrate_documents(sqlite_conn, pg_conn):
    print("Migrating documents...")
    sqlite_cursor = sqlite_conn.cursor()
    pg_cursor = pg_conn.cursor()
    
    sqlite_cursor.execute("SELECT * FROM documents")
    documents = sqlite_cursor.fetchall()
    
    count = 0
    for doc in documents:
        try:
            # Insert document
            # Map original_filename -> filename
            # Map filename -> file_path (assuming it's the stored path)
            pg_cursor.execute("""
                INSERT INTO documents (id, filename, file_path, file_size, mime_type, owner_id, status, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
            """, (
                doc['id'],
                doc['original_filename'], # filename in Postgres
                doc['filename'],          # file_path in Postgres
                doc['file_size'],
                doc['content_type'],
                doc['user_id'],
                doc['processing_status'].upper() if doc['processing_status'] else 'PENDING',
                doc['upload_date'],
                doc['upload_date'] # Use upload_date for updated_at too
            ))
            
            # Insert analysis result if exists
            if doc['analysis_result']:
                pg_cursor.execute("""
                    INSERT INTO analysis_results (document_id, summary, key_figures, vector_db_path, created_at)
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    doc['id'],
                    doc['analysis_result'],
                    '[]', # Empty JSON list for key_figures
                    '',   # Empty vector_db_path
                    doc['upload_date']
                ))
            
            count += 1
        except Exception as e:
            print(f"Error migrating document {doc['id']}: {e}")
            
    pg_conn.commit()
    print(f"Migrated {count} documents.")

def migrate_analytics(sqlite_conn, pg_conn):
    print("Migrating analytics events...")
    sqlite_cursor = sqlite_conn.cursor()
    pg_cursor = pg_conn.cursor()
    
    sqlite_cursor.execute("SELECT * FROM analytics_events")
    events = sqlite_cursor.fetchall()
    
    count = 0
    for event in events:
        try:
            pg_cursor.execute("""
                INSERT INTO analytics_events (id, user_id, event_type, event_data, created_at)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
            """, (
                event['id'],
                event['user_id'],
                event['event_type'],
                event['event_metadata'], # Assuming it's already a JSON string
                event['timestamp']
            ))
            count += 1
        except Exception as e:
            print(f"Error migrating event {event['id']}: {e}")
            
    pg_conn.commit()
    print(f"Migrated {count} analytics events.")

def migrate_token_usage(sqlite_conn, pg_conn):
    print("Migrating token usage...")
    sqlite_cursor = sqlite_conn.cursor()
    pg_cursor = pg_conn.cursor()
    
    sqlite_cursor.execute("SELECT * FROM token_usage")
    usages = sqlite_cursor.fetchall()
    
    count = 0
    for usage in usages:
        try:
            pg_cursor.execute("""
                INSERT INTO token_usage (id, user_id, model_name, prompt_tokens, completion_tokens, total_tokens, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
            """, (
                usage['id'],
                usage['user_id'],
                usage['model_name'],
                usage['input_tokens'],
                usage['output_tokens'],
                usage['total_tokens'],
                usage['timestamp']
            ))
            count += 1
        except Exception as e:
            print(f"Error migrating token usage {usage['id']}: {e}")
            
    pg_conn.commit()
    print(f"Migrated {count} token usage records.")

def reset_sequences(pg_conn):
    print("Resetting sequences...")
    pg_cursor = pg_conn.cursor()
    tables = ['users', 'documents', 'analytics_events', 'token_usage', 'analysis_results']
    
    for table in tables:
        try:
            pg_cursor.execute(f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), COALESCE((SELECT MAX(id) + 1 FROM {table}), 1), false);")
        except Exception as e:
            print(f"Error resetting sequence for {table}: {e}")
            pg_conn.rollback()
            continue
            
    pg_conn.commit()
    print("Sequences reset.")

def main():
    print("Starting migration...")
    sqlite_conn = get_sqlite_conn()
    pg_conn = get_postgres_conn()
    
    try:
        migrate_users(sqlite_conn, pg_conn)
        migrate_documents(sqlite_conn, pg_conn)
        migrate_analytics(sqlite_conn, pg_conn)
        migrate_token_usage(sqlite_conn, pg_conn)
        reset_sequences(pg_conn)
        print("Migration completed successfully.")
    except Exception as e:
        print(f"Migration failed: {e}")
    finally:
        sqlite_conn.close()
        pg_conn.close()

if __name__ == "__main__":
    main()

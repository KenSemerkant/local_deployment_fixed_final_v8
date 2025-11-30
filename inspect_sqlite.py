import sqlite3
import os

db_files = [
    "microservices/document-service/documents.db",
    "microservices/data/user-service/db/users.db",
    "backend/local_data/db/financial_analyst.db"
]

for db_file in db_files:
    print(f"--- Inspecting {db_file} ---")
    if not os.path.exists(db_file):
        print("File not found.")
        continue
        
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        # List tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"Tables: {[t[0] for t in tables]}")
        
        for table in tables:
            table_name = table[0]
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                print(f"  - {table_name}: {count} rows")
                
                # Get columns
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = [info[1] for info in cursor.fetchall()]
                print(f"    Columns: {columns}")
                
                # Get sample data
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 1")
                row = cursor.fetchone()
                print(f"    Sample: {row}")
            except Exception as e:
                print(f"  - {table_name}: Error counting rows ({e})")
                
        conn.close()
    except Exception as e:
        print(f"Error inspecting DB: {e}")
    print("\n")

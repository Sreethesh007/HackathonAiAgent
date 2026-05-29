import sqlite3
import os
from pathlib import Path
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Supabase client
supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_KEY")

if not supabase_url or not supabase_key:
    print("Error: SUPABASE_URL or SUPABASE_KEY not found in environment.")
    exit(1)

supabase: Client = create_client(supabase_url, supabase_key)

DB_APPOINTMENTS = Path("data/appointments.db")
DB_CONVERSATIONS = Path("data/conversations.db")

def migrate_appointments():
    if not DB_APPOINTMENTS.exists():
        print(f"Skipping appointments migration: {DB_APPOINTMENTS} does not exist.")
        return

    print("Migrating appointments...")
    with sqlite3.connect(DB_APPOINTMENTS) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM appointments")
        rows = cursor.fetchall()
        
        if not rows:
            print("No appointments to migrate.")
            return
            
        data = [dict(row) for row in rows]
        
        # Batch insert
        try:
            # We can insert in batches if there are many, but usually it's fine
            response = supabase.table("appointments").upsert(data).execute()
            print(f"Successfully migrated {len(data)} appointments.")
        except Exception as e:
            print(f"Error migrating appointments: {e}")

def migrate_conversations():
    if not DB_CONVERSATIONS.exists():
        print(f"Skipping conversations migration: {DB_CONVERSATIONS} does not exist.")
        return

    print("Migrating conversations...")
    with sqlite3.connect(DB_CONVERSATIONS) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT id, session_id, user_id, role, message, timestamp FROM conversations")
        rows = cursor.fetchall()
        
        if not rows:
            print("No conversations to migrate.")
            return
            
        data = [dict(row) for row in rows]
        
        # Batch insert
        try:
            response = supabase.table("conversations").upsert(data).execute()
            print(f"Successfully migrated {len(data)} conversations.")
        except Exception as e:
            print(f"Error migrating conversations: {e}")

if __name__ == "__main__":
    print("Starting migration to Supabase...")
    migrate_appointments()
    migrate_conversations()
    print("Migration complete!")

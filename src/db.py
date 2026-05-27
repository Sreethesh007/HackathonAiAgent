import sqlite3
import json
from pathlib import Path
from src.config import settings

DB_PATH = Path("./data/appointments.db")

def init_db():
    """Initialize the SQLite database for appointments."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS appointments (
                appointment_id TEXT PRIMARY KEY,
                datetime_iso TEXT,
                provider TEXT,
                location TEXT,
                patient_name TEXT,
                patient_age TEXT,
                reason TEXT,
                session_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()

def add_appointment(data: dict):
    """Insert a new appointment."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR IGNORE INTO appointments (
                appointment_id, datetime_iso, provider, location, 
                patient_name, patient_age, reason, session_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get("appointment_id"),
            data.get("datetime_iso"),
            data.get("provider"),
            data.get("location"),
            data.get("patient_name", "Unknown"),
            data.get("patient_age", "Unknown"),
            data.get("reason", "N/A"),
            data.get("session_id")
        ))
        conn.commit()

def get_all_appointments() -> list[dict]:
    """Fetch all appointments."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM appointments ORDER BY created_at DESC")
        rows = cursor.fetchall()
        
        # Convert sqlite3.Row objects to standard dicts
        return [dict(row) for row in rows]

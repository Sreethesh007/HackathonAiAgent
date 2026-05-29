"""
Conversation persistence layer — Supabase integration.
"""

from __future__ import annotations
from typing import Literal
from src.config import settings
from supabase import create_client, Client

supabase: Client = create_client(settings.supabase_url, settings.supabase_key)

def init_db(db_path: str | None = None) -> None:
    """No-op: Supabase tables should be created via SQL editor."""
    pass

def save_message(
    session_id: str,
    user_id: str,
    role: Literal["user", "assistant"],
    message: str,
) -> int:
    """Persist a single conversation turn and return the new row id."""
    try:
        response = supabase.table("conversations").insert({
            "session_id": session_id,
            "user_id": user_id,
            "role": role,
            "message": message
        }).execute()
        if response.data:
            return response.data[0].get("id", 0)
    except Exception as e:
        print(f"Failed to save message to Supabase: {e}")
    return 0

def get_messages(session_id: str) -> list[dict]:
    """Fetch all conversation turns for a session, ordered by timestamp."""
    try:
        response = supabase.table("conversations").select("*").eq("session_id", session_id).order("timestamp").order("id").execute()
        return response.data
    except Exception as e:
        print(f"Failed to fetch messages from Supabase: {e}")
        return []

def delete_session(session_id: str) -> int:
    """Remove all messages for a session."""
    try:
        response = supabase.table("conversations").delete().eq("session_id", session_id).execute()
        return len(response.data) if response.data else 0
    except Exception as e:
        print(f"Failed to delete session from Supabase: {e}")
        return 0

def get_user_sessions(user_id: str) -> list[dict]:
    """Fetch all unique sessions for a user directly from Supabase, computing summaries."""
    try:
        response = supabase.table("conversations").select("session_id, timestamp, role, message").eq("user_id", user_id).order("timestamp").execute()
        if not response.data:
            return []
            
        sessions = {}
        for row in response.data:
            sid = row["session_id"]
            if sid not in sessions:
                sessions[sid] = {
                    "session_id": sid,
                    "created_at": row["timestamp"],
                    "updated_at": row["timestamp"],
                    "status": "completed", # Assumed completed if loaded from history
                    "summary": row["message"][:50] if row["role"] == "user" else "Chat session"
                }
            else:
                sessions[sid]["updated_at"] = row["timestamp"]
                # If we didn't get a user message yet for summary, grab it
                if row["role"] == "user" and sessions[sid]["summary"] == "Chat session":
                    sessions[sid]["summary"] = row["message"][:50]
                    
        return list(sessions.values())
    except Exception as e:
        print(f"Failed to fetch user sessions from Supabase: {e}")
        return []

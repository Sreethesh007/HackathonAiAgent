from src.config import settings
from supabase import create_client, Client
from datetime import datetime, timedelta

supabase: Client = create_client(settings.supabase_url, settings.supabase_key)

def init_db():
    """No-op: Supabase tables should be created via SQL editor."""
    pass

def check_slot_availability(datetime_iso: str) -> bool:
    """
    Returns True if the requested slot is FREE (no existing appointment within ±30 min).
    Returns False if it is TAKEN.
    """
    try:
        requested = datetime.fromisoformat(datetime_iso.replace("Z", "+00:00"))
        window_start = (requested - timedelta(minutes=30)).isoformat()
        window_end   = (requested + timedelta(minutes=30)).isoformat()

        response = (
            supabase.table("appointments")
            .select("appointment_id, datetime_iso")
            .gte("datetime_iso", window_start)
            .lte("datetime_iso", window_end)
            .execute()
        )
        return len(response.data) == 0   # True = free, False = taken
    except Exception as e:
        print(f"Failed to check slot availability: {e}")
        # Fail open — if we can't check, assume free so booking isn't blocked
        return True

def add_appointment(data: dict):
    """Insert a new appointment."""
    try:
        supabase.table("appointments").upsert({
            "appointment_id":  data.get("appointment_id"),
            "datetime_iso":    data.get("datetime_iso"),
            "provider":        data.get("provider"),
            "location":        data.get("location"),
            "patient_name":    data.get("patient_name", "Unknown"),
            "patient_age":     data.get("patient_age", "Unknown"),
            "gender":          data.get("gender", ""),
            "primary_concern": data.get("primary_concern", "N/A"),
            "reason":          data.get("reason", "N/A"),
            "session_id":      data.get("session_id"),
        }).execute()
    except Exception as e:
        print(f"Failed to add appointment to Supabase: {e}")

def get_all_appointments() -> list[dict]:
    """Fetch all appointments."""
    try:
        response = supabase.table("appointments").select("*").order("created_at", desc=True).execute()
        return response.data
    except Exception as e:
        print(f"Failed to get appointments from Supabase: {e}")
        return []

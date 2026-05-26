"""
Concrete tool implementations called by specialist agents.

Every tool:
  - Has a clear typed signature
  - Catches its own exceptions and re-raises as ToolError
  - Logs execution time and status to Prometheus
  - Retried automatically by agents via tenacity
"""

from __future__ import annotations

import time
import uuid
from datetime import datetime, timedelta
from typing import Any

from src.observability.logging import get_logger
from src.observability.metrics import TOOL_CALLS

log = get_logger(__name__)


class ToolError(Exception):
    """Raised when a tool call fails after retries are exhausted."""
    pass


def _track(tool_name: str):
    """Decorator: Prometheus counter + structured log around any tool call."""
    def decorator(fn):
        async def wrapper(*args, **kwargs):
            start = time.perf_counter()
            try:
                result = await fn(*args, **kwargs) if _is_async(fn) else fn(*args, **kwargs)
                TOOL_CALLS.labels(tool=tool_name, status="success").inc()
                log.debug("tool_success", tool=tool_name, latency_ms=round((time.perf_counter()-start)*1000))
                return result
            except ToolError:
                raise
            except Exception as exc:
                TOOL_CALLS.labels(tool=tool_name, status="error").inc()
                log.error("tool_error", tool=tool_name, error=str(exc))
                raise ToolError(f"[{tool_name}] {exc}") from exc
        import asyncio
        def _is_async(f): return asyncio.iscoroutinefunction(f)
        return wrapper
    return decorator


# ── Symptom & Triage Tools ─────────────────────────────────────────────────

SYMPTOM_SEVERITY_MAP: dict[str, int] = {
    # Life-threatening (8-10)
    "chest pain": 9, "cardiac arrest": 10, "stroke": 10, "difficulty breathing": 9,
    "severe bleeding": 9, "unconscious": 10, "anaphylaxis": 10, "seizure": 8,
    # Urgent (5-7)
    "high fever": 7, "severe headache": 7, "vomiting blood": 8, "abdominal pain": 6,
    "broken bone": 6, "deep cut": 6, "confusion": 7, "fainting": 7,
    # Moderate (3-4)
    "headache": 4, "nausea": 3, "dizziness": 4, "mild fever": 3, "earache": 3,
    # Routine (1-2)
    "sore throat": 2, "cold": 1, "cough": 2, "minor cut": 1, "rash": 2,
}


def symptom_lookup(symptom: str) -> dict[str, Any]:
    """
    Look up severity score and basic information for a given symptom.

    Args:
        symptom: Plain-language symptom description (e.g. "chest pain")

    Returns:
        dict with keys: severity_score, urgency_hint, first_aid_tip
    """
    symptom_lower = symptom.lower().strip()

    # Find best matching key
    score = 0
    matched_key = None
    for key, sev in SYMPTOM_SEVERITY_MAP.items():
        if key in symptom_lower or symptom_lower in key:
            if sev > score:
                score = sev
                matched_key = key

    urgency = (
        "emergency" if score >= 8
        else "urgent" if score >= 5
        else "routine" if score >= 1
        else "unknown"
    )

    return {
        "symptom": symptom,
        "matched_key": matched_key or "not_found",
        "severity_score": score,
        "urgency_hint": urgency,
        "first_aid_tip": _first_aid_tip(urgency),
    }


def _first_aid_tip(urgency: str) -> str:
    tips = {
        "emergency": "Call 112 or go to the nearest emergency room immediately.",
        "urgent": "Seek medical attention within the next few hours.",
        "routine": "Schedule an appointment with your primary care physician.",
        "unknown": "Monitor symptoms and consult a healthcare provider if they worsen.",
    }
    return tips.get(urgency, tips["unknown"])


def severity_scale(symptoms: list[str]) -> dict[str, Any]:
    """
    Aggregate severity score across multiple symptoms.

    Returns the maximum individual score and a combined urgency level.
    """
    if not symptoms:
        return {"max_score": 0, "urgency_level": "unknown", "individual_scores": []}

    results = [symptom_lookup(s) for s in symptoms]
    max_score = max(r["severity_score"] for r in results)

    urgency = (
        "emergency" if max_score >= 8
        else "urgent" if max_score >= 5
        else "routine" if max_score >= 1
        else "unknown"
    )

    return {
        "max_score": max_score,
        "urgency_level": urgency,
        "individual_scores": [
            {"symptom": r["symptom"], "score": r["severity_score"]} for r in results
        ],
    }


# ── Scheduling Tools ────────────────────────────────────────────────────────

def check_availability(date_range: str, urgency: str = "routine") -> list[dict[str, str]]:
    """
    Return available appointment slots for the given date range.

    In production this calls your calendar/EHR API.
    This implementation generates realistic mock slots.

    Args:
        date_range: Natural-language or ISO range, e.g. "next week" or "2025-06-01..2025-06-07"
        urgency: "emergency" | "urgent" | "routine"

    Returns:
        List of slot dicts with: slot_id, datetime_iso, provider, location, slot_type
    """
    base = datetime.utcnow()
    offset_days = {"emergency": 0, "urgent": 1, "routine": 3}.get(urgency, 3)

    slots = []
    for i in range(3):
        slot_dt = base + timedelta(days=offset_days + i, hours=9 + i * 2)
        slots.append({
            "slot_id": str(uuid.uuid4())[:8],
            "datetime_iso": slot_dt.isoformat(),
            "provider": f"Dr. {'ABC'[i]}. Smith",
            "location": "City Medical Center — Room 10" + str(i + 1),
            "slot_type": "telemedicine" if urgency == "routine" else "in_person",
        })
    return slots


def book_appointment(slot_id: str, patient_id: str, reason: str = "") -> dict[str, Any]:
    """
    Confirm and book an appointment slot for a patient.

    Args:
        slot_id:    Slot identifier returned by check_availability
        patient_id: Patient's unique identifier   ⚠ PII
        reason:     Brief clinical reason for visit

    Returns:
        dict with: appointment_id, confirmation_code, status, message
    """
    appointment_id = "APT-" + str(uuid.uuid4())[:8].upper()
    confirmation = "CONF-" + str(uuid.uuid4())[:6].upper()

    log.info(
        "appointment_booked",
        appointment_id=appointment_id,
        slot_id=slot_id,
        patient_id=patient_id,   # redacted in production logs by PII processor
    )

    return {
        "appointment_id": appointment_id,
        "confirmation_code": confirmation,
        "slot_id": slot_id,
        "status": "confirmed",
        "message": f"Appointment {appointment_id} confirmed. Reference: {confirmation}.",
    }

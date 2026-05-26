"""API Pydantic schemas — request and response models."""

from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel, Field


class TriageRequest(BaseModel):
    patient_id: str | None = Field(None, description="Unique patient identifier (optional, auto-derived from token if missing)")
    message: str = Field(..., min_length=5, max_length=2000, description="Patient's symptom description")
    session_id: str | None = Field(None, description="Reuse existing session for follow-up")

    model_config = {"json_schema_extra": {
        "examples": [{"message": "I have severe chest pain radiating to my left arm"}]
    }}


class TriageResponse(BaseModel):
    session_id: str
    response: str
    severity_score: int
    urgency_level: str
    primary_concern: str
    sources: list[str]
    guidelines_applied: list[str]
    appointment_booked: bool
    appointment_id: str | None
    appointment_datetime: str | None
    appointment_provider: str | None
    requires_human_review: bool
    quality_score: float
    iteration_count: int
    reasoning_trace: list[str]


class ContinueRequest(BaseModel):
    message: str | None = Field(None, description="Follow-up patient message")
    patient_id: str | None = Field(None, description="Patient ID (required for new message turns)")
    human_approval: bool | None = Field(None, description="Human reviewer decision for HITL sessions")


class ContinueResponse(BaseModel):
    session_id: str
    response: str
    flow_status: str
    requires_human_review: bool
    severity_score: int
    urgency_level: str


class SessionStatusResponse(BaseModel):
    session_id: str
    flow_status: str
    iteration_count: int
    max_iterations: int
    requires_human_review: bool
    severity_score: int
    urgency_level: str
    appointment_booked: bool
    appointment_id: str | None
    created_at: str
    updated_at: str


class HealthResponse(BaseModel):
    status: str
    version: str
    uptime_seconds: int
    environment: str
    pipeline_ready: bool
    llm_provider: str = ""
    llm_model: str = ""


class ProviderInfoResponse(BaseModel):
    ok: bool
    provider: str
    model: str = ""
    latency_ms: int = 0
    error: str | None = None
    base_url: str | None = None       # llama.cpp only
    n_ctx: int | None = None          # llama.cpp only
    n_gpu_layers: int | None = None   # llama.cpp only
    api_key_set: bool | None = None   # anthropic only


class ErrorDetail(BaseModel):
    type: str
    title: str
    status: int
    detail: str
    instance: str


# ── Conversation persistence ──────────────────────────────────────────────────

class ConversationMessage(BaseModel):
    """A single stored conversation turn returned by GET /api/conversations/{session_id}."""
    id: int
    session_id: str
    user_id: str
    role: str                # "user" | "assistant"
    message: str
    timestamp: str


class SaveMessageRequest(BaseModel):
    """Payload for POST /api/conversations — saves a single message turn."""
    session_id: str = Field(..., description="Triage session UUID")
    user_id: str | None = Field(None, description="Patient identifier (falls back to JWT sub)")
    role: str = Field(..., description='"user" or "assistant"')
    message: str = Field(..., min_length=1, max_length=8000, description="Message text")

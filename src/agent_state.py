"""
AgentState — the single shared data structure flowing through the entire
LangGraph pipeline. Every agent reads from and writes to this object.

Design principles:
  - Pydantic v2 for runtime validation + IDE autocomplete
  - All PII fields clearly marked for redaction in logs
  - Versioned for forward-compatible schema evolution
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Annotated, Any

from pydantic import BaseModel, Field, field_validator, model_validator


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class UrgencyLevel(str, Enum):
    EMERGENCY = "emergency"   # Call 911 / go to ER immediately
    URGENT    = "urgent"      # See a doctor within 24 hours
    ROUTINE   = "routine"     # Schedule a regular appointment
    UNKNOWN   = "unknown"     # Not yet assessed


class AgentName(str, Enum):
    ORCHESTRATOR = "orchestrator"
    TRIAGE       = "triage"
    RESEARCH     = "research"
    SCHEDULER    = "scheduler"
    CRITIC       = "critic"
    HUMAN_REVIEW = "human_review"
    SYNTHESIZER  = "synthesizer"


class FlowStatus(str, Enum):
    RUNNING        = "running"
    AWAITING_HUMAN = "awaiting_human"   # HITL pause
    COMPLETED      = "completed"
    FAILED         = "failed"


# ---------------------------------------------------------------------------
# Sub-models
# ---------------------------------------------------------------------------

class Message(BaseModel):
    """A single turn in the patient conversation."""
    role: str                    # "user" | "assistant" | "agent"
    content: str                 # ⚠ PII — redact in production logs
    agent: AgentName | None = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class TriageResult(BaseModel):
    """Output produced by TriageAgent."""
    severity_score: int = Field(0, ge=0, le=10)   # 0 = not assessed, 10 = life-threatening
    urgency_level: UrgencyLevel = UrgencyLevel.UNKNOWN
    primary_concern: str = ""
    abcde_assessment: dict[str, str] = Field(default_factory=dict)
    reasoning: str = ""

    @model_validator(mode="before")
    @classmethod
    def clamp_severity(cls, data):
        if isinstance(data, dict) and "severity_score" in data:
            data["severity_score"] = max(0, min(10, int(data["severity_score"])))
        return data


class ResearchResult(BaseModel):
    """Output produced by ResearchAgent."""
    sources: list[dict[str, str]] = Field(default_factory=list)
    summary: str = ""
    confidence_score: float = Field(0.0, ge=0.0, le=1.0)
    guidelines_applied: list[str] = Field(default_factory=list)


class AppointmentResult(BaseModel):
    """Output produced by SchedulerAgent."""
    appointment_id: str = ""
    datetime_iso: str = ""
    location: str = ""
    provider: str = ""
    confirmation_message: str = ""
    booked: bool = False


class CriticResult(BaseModel):
    """Output produced by CriticAgent."""
    quality_score: float = Field(0.0, ge=0.0, le=1.0)
    issues_found: list[str] = Field(default_factory=list)
    approved: bool = False
    requires_human_review: bool = False
    feedback: str = ""


# ---------------------------------------------------------------------------
# Root state
# ---------------------------------------------------------------------------

class AgentState(BaseModel):
    """
    Central state object flowing through the LangGraph StateGraph.

    Fields marked ⚠ PII are hashed in production-mode structured logs.
    Version field allows non-breaking schema evolution.
    """

    # Metadata
    schema_version: str = "1.0.0"
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    patient_id: str = ""       # ⚠ PII
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Conversation
    messages: list[Message] = Field(default_factory=list)
    current_input: str = ""    # ⚠ PII — latest user message

    # Routing
    next_agent: AgentName | None = None
    iteration_count: int = 0
    max_iterations: int = 10
    flow_status: FlowStatus = FlowStatus.RUNNING

    # Agent outputs (populated as pipeline progresses)
    triage: TriageResult = Field(default_factory=TriageResult)
    research: ResearchResult = Field(default_factory=ResearchResult)
    appointment: AppointmentResult = Field(default_factory=AppointmentResult)
    critic: CriticResult = Field(default_factory=CriticResult)

    # Final synthesized response
    final_response: str = ""

    # Human-in-the-loop
    requires_human_review: bool = False
    human_approved: bool | None = None  # None = not yet decided

    # Reasoning trace (populated by orchestrator — useful for debugging)
    reasoning_trace: list[str] = Field(default_factory=list)

    # Arbitrary metadata agents can attach (e.g. tool call counts)
    metadata: dict[str, Any] = Field(default_factory=dict)

    # ---------------------------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------------------------

    def add_message(self, role: str, content: str, agent: AgentName | None = None) -> None:
        self.messages.append(Message(role=role, content=content, agent=agent))
        self.updated_at = datetime.utcnow()

    def add_trace(self, step: str) -> None:
        self.reasoning_trace.append(f"[{datetime.utcnow().isoformat()}] {step}")

    def increment_iteration(self) -> None:
        self.iteration_count += 1
        self.updated_at = datetime.utcnow()

    def is_exhausted(self) -> bool:
        """True if we've hit the max iteration ceiling."""
        return self.iteration_count >= self.max_iterations

    def safe_log_dict(self) -> dict:
        """Return a dict safe to write to logs — PII fields are masked."""
        import hashlib
        d = self.model_dump(mode="json")
        if d.get("patient_id"):
            d["patient_id"] = hashlib.sha256(d["patient_id"].encode()).hexdigest()[:12]
        if d.get("current_input"):
            d["current_input"] = "<redacted>"
        for msg in d.get("messages", []):
            msg["content"] = "<redacted>"
        return d

    class Config:
        use_enum_values = True

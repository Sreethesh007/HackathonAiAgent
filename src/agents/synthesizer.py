"""
Synthesizer
-----------
The final node in the LangGraph pipeline.

Takes everything in AgentState and produces one clear, compassionate,
patient-facing response. This is the only text the patient sees.

Also handles the human_review pause node (HITL).
"""

from __future__ import annotations

import json
import time

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from src.agent_state import AgentName, AgentState, FlowStatus, UrgencyLevel
from src.config import settings
from src.llm.provider import get_llm
from src.observability.logging import get_logger
from src.observability.metrics import AGENT_CALLS, AGENT_LATENCY, FLOW_COMPLETIONS, HUMAN_REVIEWS

log = get_logger(__name__)

SYNTHESIZER_SYSTEM_PROMPT = """You are a compassionate healthcare communication specialist.
Your job is to turn structured medical triage data into a clear, warm, and reassuring
patient-facing response.

Guidelines:
- Lead with the most important action (e.g. "Call 112 now" for emergencies)
- Use plain language — no medical jargon
- Be empathetic but calm and clear
- For emergencies (severity >= 8): open with urgent call-to-action, be direct
- For urgent cases: explain timeline clearly, provide next steps
- For routine cases: reassure, explain scheduling, add general wellness tips
- If `offer_appointment` is true, explicitly ask the user if they would like you to book an appointment for them, or if they have any specific time preferences.
- Always end with: "If your symptoms worsen suddenly, seek emergency care immediately."
- Keep response under 250 words
- If an appointment is booked, confirm the date, time, provider, and location clearly and warmly.

You will receive structured JSON — respond ONLY with the text of the message you want to send to the patient (plain prose, no JSON)."""


class Synthesizer:
    """Produces the final patient-facing response from the full pipeline state."""

    def __init__(self, llm: BaseChatModel | None = None) -> None:
        self.llm = llm or get_llm(temperature=0.3, max_tokens=400)
        self.name = AgentName.SYNTHESIZER

    def synthesize(self, state: AgentState) -> AgentState:
        """Generate the final patient response and close the flow."""
        start = time.perf_counter()
        log.info("synthesizer_start", session_id=state.session_id)
        state.add_trace("SYNTHESIZER: Generating final patient response")

        # If already failed/set, just clean up
        if state.flow_status == FlowStatus.FAILED and state.final_response:
            state.flow_status = FlowStatus.COMPLETED
            return state

        try:
            state.final_response = self._generate_response(state)
            state.flow_status = FlowStatus.COMPLETED
            state.add_message("assistant", state.final_response)

            urgency = str(state.triage.urgency_level).lower().split(".")[-1]
            FLOW_COMPLETIONS.labels(urgency_level=urgency).inc()
            AGENT_CALLS.labels(agent="synthesizer", status="success").inc()
            state.add_trace("SYNTHESIZER: Done")

        except Exception as exc:
            log.error("synthesizer_error", error=str(exc), session_id=state.session_id)
            state.final_response = self._emergency_fallback(state)
            state.flow_status = FlowStatus.COMPLETED
            AGENT_CALLS.labels(agent="synthesizer", status="error").inc()

        AGENT_LATENCY.labels(agent="synthesizer").observe(time.perf_counter() - start)
        return state

    def _generate_response(self, state: AgentState) -> str:
        """Build structured context and call LLM for final response."""
        appt_section = ""
        if state.appointment.booked:
            appt_section = (
                f"appointment_id: {state.appointment.appointment_id}\n"
                f"appointment_datetime: {state.appointment.datetime_iso}\n"
                f"provider: {state.appointment.provider}\n"
                f"location: {state.appointment.location}"
            )

        context = {
            "patient_message": state.current_input,
            "severity_score": state.triage.severity_score,
            "urgency_level": str(state.triage.urgency_level),
            "primary_concern": state.triage.primary_concern,
            "clinical_recommendation": state.research.summary,
            "key_guidelines": state.research.guidelines_applied[:3],
            "appointment": appt_section or "not_booked",
            "offer_appointment": getattr(state, "offer_appointment", False),
            "requires_human_review": state.requires_human_review,
            "human_approved": state.human_approved,
            "quality_score": state.critic.quality_score,
            "critic_feedback": state.critic.feedback[:200] if state.critic.feedback else "",
        }

        response = self.llm.invoke([
            SystemMessage(content=SYNTHESIZER_SYSTEM_PROMPT),
            HumanMessage(content=json.dumps(context, indent=2)),
        ])
        content = response.content.strip()
        if not content:
            raise ValueError("LLM returned an empty response")
        return content

    def _emergency_fallback(self, state: AgentState) -> str:
        """Hard-coded safe fallback when LLM call fails entirely."""
        if state.triage.severity_score >= 8:
            return (
                "⚠️ IMPORTANT: Based on your symptoms, you may need emergency medical care. "
                "Please call 112 or go to your nearest emergency room immediately. "
                "Do not wait or drive yourself."
            )
        return (
            "Thank you for using our triage service. Based on your symptoms, "
            "please contact your healthcare provider promptly. "
            "If your symptoms worsen suddenly, seek emergency care immediately."
        )


class HumanReviewNode:
    """
    HITL (Human-in-the-Loop) pause node.

    When the critic score is below threshold, the graph pauses here.
    A human reviewer can:
      - Approve (state.human_approved = True) → pipeline continues to synthesizer
      - Reject (state.human_approved = False) → session marked for manual follow-up
    """

    def pause(self, state: AgentState) -> AgentState:
        """Mark the session as awaiting human review and log."""
        state.flow_status = FlowStatus.AWAITING_HUMAN
        HUMAN_REVIEWS.inc()
        log.warning(
            "human_review_required",
            session_id=state.session_id,
            quality_score=state.critic.quality_score,
            issues=state.critic.issues_found,
        )
        state.add_trace(
            f"HUMAN_REVIEW: Paused — score={state.critic.quality_score:.2f}, "
            f"issues={state.critic.issues_found}"
        )
        return state

    def resume(self, state: AgentState, approved: bool) -> AgentState:
        """Called by the API when a human reviewer submits their decision."""
        state.human_approved = approved
        state.flow_status = FlowStatus.RUNNING
        state.requires_human_review = False
        action = "approved" if approved else "rejected"
        state.add_trace(f"HUMAN_REVIEW: Reviewer {action} the response")
        log.info("human_review_resolved", session_id=state.session_id, approved=approved)
        return state

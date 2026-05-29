"""
SchedulerAgent
--------------
Books medical appointments based on triage urgency and patient preference.
Uses check_availability() and book_appointment() tools from clinical_tools.
"""

from __future__ import annotations

import json
import time
from src.utils import extract_json

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from tenacity import retry, stop_after_attempt, wait_exponential

from src.agent_state import AgentName, AgentState, AppointmentResult
from src.config import settings
from src.llm.provider import get_llm
from src.observability.logging import get_logger
from src.observability.metrics import AGENT_CALLS, AGENT_LATENCY
from src.tools.clinical_tools import book_appointment, check_availability

log = get_logger(__name__)

SCHEDULER_SYSTEM_PROMPT = """You are a medical appointment scheduling assistant AI.
You will receive:
1. The patient's urgency level and primary concern
2. Available appointment slots

Select the BEST slot for this patient based on:
- Urgency: emergency/urgent → earliest slot; routine → any available
- Patient preference mentioned in their message (if any)

Output a JSON object with EXACTLY these keys:
{
  "selected_slot_id": "<slot_id from the available slots>",
  "reasoning": "<why you chose this slot>",
  "appointment_type": "<telemedicine|in_person>",
  "pre_appointment_advice": "<what the patient should do before the appointment>",
  "patient_name": "<extract name from message, or null>",
  "patient_age": "<extract age from message, or null>",
  "requested_datetime_iso": "<if the user explicitly requested a specific date/time, provide it in ISO8601 format (e.g. 2026-06-04T12:00:00). If it is a past date, output null. If not requested, output null>"
}

CRITICAL: selected_slot_id must exactly match one of the provided slot IDs.
First character of your response must be {."""


class SchedulerAgent:
    """Books appointments using availability tools + LLM slot selection."""

    def __init__(self, llm: BaseChatModel | None = None) -> None:
        self.llm = llm or get_llm(temperature=0.0, max_tokens=256)
        self.name = AgentName.SCHEDULER

    def book(self, state: AgentState) -> AgentState:
        """Check availability, select best slot, confirm booking."""
        start = time.perf_counter()
        urgency = str(state.triage.urgency_level).lower().split(".")[-1]
        log.info("scheduler_book_start", session_id=state.session_id, urgency=urgency)
        state.add_trace(f"SCHEDULER: Checking availability for urgency={urgency}")

        try:
            slots = check_availability(date_range="next_available", urgency=urgency)
            try:
                selected, parsed_data = self._select_slot(state, slots)
            except Exception as e:
                log.warning("llm_slot_selection_failed", error=str(e), session_id=state.session_id)
                selected = slots[0]
                parsed_data = {}

            confirmation = book_appointment(
                slot_id=selected["slot_id"],
                patient_id=state.patient_id,
                reason=state.triage.primary_concern,
            )

            # Find the slot details
            slot_detail = next((s for s in slots if s["slot_id"] == selected["slot_id"]), slots[0])
            
            final_datetime = slot_detail["datetime_iso"]
            req_dt = parsed_data.get("requested_datetime_iso")
            if req_dt:
                try:
                    from datetime import datetime
                    req_dt_parsed = datetime.fromisoformat(req_dt.replace("Z", "+00:00"))
                    if req_dt_parsed > datetime.utcnow():
                        final_datetime = req_dt_parsed.isoformat()
                except Exception:
                    pass

            state.appointment = AppointmentResult(
                appointment_id=confirmation["appointment_id"],
                datetime_iso=final_datetime,
                location=slot_detail["location"],
                provider=slot_detail["provider"],
                confirmation_message=confirmation["message"],
                booked=True,
                patient_name=parsed_data.get("patient_name") or "Unknown",
                patient_age=str(parsed_data.get("patient_age") or "Unknown")
            )
            state.offer_appointment = False  # Clear flag so we don't ask again
            state.add_message(
                "agent",
                f"Appointment booked: {confirmation['appointment_id']} with {slot_detail['provider']}",
                AgentName.SCHEDULER,
            )
            state.add_trace(f"SCHEDULER: Booked {confirmation['appointment_id']}")
            AGENT_CALLS.labels(agent="scheduler", status="success").inc()

        except Exception as exc:
            log.error("scheduler_error", error=str(exc), session_id=state.session_id)
            state.appointment = AppointmentResult(
                confirmation_message="Unable to automatically book an appointment. Please call us directly.",
                booked=False,
            )
            state.add_trace(f"SCHEDULER ERROR: {exc}")
            AGENT_CALLS.labels(agent="scheduler", status="error").inc()

        AGENT_LATENCY.labels(agent="scheduler").observe(time.perf_counter() - start)
        return state

    @retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=1, max=4), reraise=True)
    def _select_slot(self, state: AgentState, slots: list[dict]) -> tuple[dict, dict]:
        """LLM selects the best slot; falls back to first slot on parse error."""
        slots_text = json.dumps(slots, indent=2)
        conversation = "\n".join([f"{msg.role}: {msg.content}" for msg in state.messages])
        prompt = (
            f"Urgency level: {state.triage.urgency_level}\n"
            f"Primary concern: {state.triage.primary_concern}\n"
            f"Patient conversation:\n{conversation}\n\n"
            f"Available slots:\n{slots_text}\n\n"
            "Select the best slot and return JSON."
        )
        response = self.llm.invoke([
            SystemMessage(content=SCHEDULER_SYSTEM_PROMPT),
            HumanMessage(content=prompt),
        ])
        data = extract_json(response.content.strip())
        selected_id = data.get("selected_slot_id", slots[0]["slot_id"])
        matched = next((s for s in slots if s["slot_id"] == selected_id), slots[0])
        return matched, data


# ─────────────────────────────────────────────────────────────────────────────

"""
CriticAgent
-----------
Quality-gates the pipeline before delivering a response to the patient.

Evaluates:
  1. Was triage completed with a valid severity score?
  2. Are research recommendations coherent and relevant?
  3. Does the urgency level match the symptoms described?
  4. Is the overall response safe to deliver?

Outputs a CriticResult with quality_score and approved flag.
Routes to human review if score < HUMAN_APPROVAL_THRESHOLD.
"""


from src.agent_state import CriticResult   # already imported AgentState above


CRITIC_SYSTEM_PROMPT = """You are a senior clinical quality reviewer AI.
Your role is to verify that a healthcare triage pipeline has produced a safe,
coherent, and appropriate response before it reaches the patient.

You will receive a summary of everything the pipeline has done so far.
Score the quality and flag any issues.

Output a JSON object with EXACTLY these keys:
{
  "quality_score": <float 0.0-1.0>,
  "approved": <true if quality_score >= 0.70, else false>,
  "issues_found": ["<issue 1>", ...],
  "feedback": "<one paragraph of constructive feedback for the pipeline>",
  "requires_human_review": <true if safety concern or score < threshold>
}

Approval criteria:
  - severity_score is 1-10 and matches symptoms described           (+0.25)
  - urgency_level is consistent with severity_score                 (+0.20)
  - research summary is coherent and non-empty                      (+0.20)
  - no obvious clinical safety error (e.g., emergency treated as routine) (+0.25)
  - response is complete (all needed steps ran)                     (+0.10)

CRITICAL: If severity >= 8 but urgency_level != "emergency" → always flag as safety issue.
Your response must start with { and end with }. 
Output raw JSON only. No greetings, no explanations, no markdown, no code blocks.
First character of your response must be {."""


class CriticAgent:
    """Reviews pipeline output quality and gates delivery to the patient."""

    def __init__(self, llm: BaseChatModel | None = None) -> None:
        self.llm = llm or get_llm(temperature=0.0, max_tokens=512)
        self.name = AgentName.CRITIC
        self.threshold = settings.human_approval_threshold

    def review(self, state: AgentState) -> AgentState:
        """Evaluate the full pipeline state. Sets state.critic and state.requires_human_review."""
        start = time.perf_counter()
        log.info("critic_review_start", session_id=state.session_id)
        state.add_trace("CRITIC: Starting quality review")

        try:
            result = self._evaluate(state)
            state.critic = result
            state.requires_human_review = result.requires_human_review

            if result.approved:
                # Offer appointment only for moderate cases (severity 3-7)
                # - Emergency (>=8): patient needs 112, not a scheduled visit
                # - Trivial (<3): no follow-up care needed
                # - Routine/urgent mid-range: appointment is appropriate
                severity = state.triage.severity_score
                urgency = str(state.triage.urgency_level).lower()
                is_moderate = 3 <= severity <= 7 and "emergency" not in urgency
                if is_moderate and not state.appointment.booked:
                    state.offer_appointment = True
                else:
                    state.offer_appointment = False
                state.add_trace(f"CRITIC: Approved (score={result.quality_score:.2f}), offer_appointment={state.offer_appointment}")
            else:
                state.add_trace(
                    f"CRITIC: NOT approved (score={result.quality_score:.2f}), "
                    f"issues={result.issues_found}, human_review={result.requires_human_review}"
                )

            state.add_message(
                "agent",
                f"Quality review: {'APPROVED' if result.approved else 'NEEDS REVIEW'} "
                f"(score={result.quality_score:.2f})",
                AgentName.CRITIC,
            )
            AGENT_CALLS.labels(agent="critic", status="success").inc()

        except Exception as exc:
            log.error("critic_error", error=str(exc), session_id=state.session_id)
            # On critic failure: conservative → require human review
            state.critic = CriticResult(
                quality_score=0.0,
                approved=False,
                requires_human_review=True,
                feedback=f"Critic failed: {exc}. Human review required.",
                issues_found=["Critic evaluation failed"],
            )
            state.requires_human_review = True
            state.add_trace(f"CRITIC ERROR: {exc} — forcing human review")
            AGENT_CALLS.labels(agent="critic", status="error").inc()

        AGENT_LATENCY.labels(agent="critic").observe(time.perf_counter() - start)
        return state

    @retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=1, max=4), reraise=True)
    def _evaluate(self, state: AgentState) -> CriticResult:
        """Build evaluation context and call LLM."""
        appt_info = (
            f"Appointment booked: {state.appointment.appointment_id} at {state.appointment.datetime_iso}"
            if state.appointment.booked
            else "No appointment booked"
        )
        summary = (
            f"Patient message: {state.current_input[:200]}\n"
            f"Triage severity: {state.triage.severity_score}/10\n"
            f"Urgency level: {state.triage.urgency_level}\n"
            f"Primary concern: {state.triage.primary_concern}\n"
            f"ABCDE assessment: {json.dumps(state.triage.abcde_assessment)}\n"
            f"Research summary: {state.research.summary[:300]}\n"
            f"Research confidence: {state.research.confidence_score:.2f}\n"
            f"Guidelines applied: {', '.join(state.research.guidelines_applied)}\n"
            f"{appt_info}\n"
            f"Iteration count: {state.iteration_count}/{state.max_iterations}\n"
            f"Human approval threshold: {self.threshold}"
        )

        response = self.llm.invoke([
            SystemMessage(content=CRITIC_SYSTEM_PROMPT),
            HumanMessage(content=summary),
        ])

        data = extract_json(response.content.strip())
        score = float(data.get("quality_score", 0.0))
        approved = score >= self.threshold and not data.get("requires_human_review", False)

        return CriticResult(
            quality_score=score,
            approved=approved,
            issues_found=data.get("issues_found", []),
            feedback=data.get("feedback", ""),
            requires_human_review=data.get("requires_human_review", not approved),
        )

"""
OrchestratorAgent
-----------------
The top-level "brain" of the pipeline.

Responsibilities:
  1. Understand the patient's goal from their message
  2. Decompose it into ordered subtasks
  3. Route each subtask to the right specialist agent
  4. Detect when the goal is satisfied and halt the pipeline
  5. Stop the pipeline if max iterations are exceeded

Uses Claude with chain-of-thought prompting via a structured system prompt.
All decisions are appended to state.reasoning_trace for full auditability.
"""

from __future__ import annotations

import time
from src.utils import extract_json

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from src.agent_state import AgentName, AgentState, FlowStatus
from src.config import settings
from src.llm.provider import get_llm
from src.observability.logging import get_logger
from src.observability.metrics import AGENT_CALLS, AGENT_LATENCY, LLM_TOKENS_USED

log = get_logger(__name__)

# ── System prompt ───────────────────────────────────────────────────────────

ORCHESTRATOR_SYSTEM_PROMPT = """You are a medical triage orchestrator AI. Your job is to:

1. Understand the patient's situation from their message.
2. Decompose the situation into an ordered list of subtasks chosen from:
   - assess_urgency    → call TriageAgent  (ALWAYS do this first for new symptoms)
   - find_guidelines   → call ResearchAgent (do after triage)
   - schedule_care     → call SchedulerAgent (only if appointment needed or requested by the user)
3. Decide which specialist agent to route to NEXT based on what has already been done.
4. Signal FINISH when all necessary subtasks are complete.

Output a JSON object with EXACTLY these keys:
{
  "reasoning": "<your chain-of-thought>",
  "subtasks": ["assess_urgency", ...],
  "next_agent": "<triage|research|scheduler|FINISH>",
  "goal_satisfied": <true|false>
}

CRITICAL RULES:
- Never provide medical diagnoses yourself.
- Always route to triage FIRST on any new patient message.
- If triage severity >= 8 (emergency), skip scheduler — just FINISH with emergency guidance.
- If the critic has already reviewed and approved, route to FINISH.
- Respond ONLY with valid JSON — no markdown fences, no prose outside the JSON."""


class OrchestratorAgent:
    """Decomposes patient goals and routes to specialist agents."""

    def __init__(self, llm: BaseChatModel | None = None) -> None:
        self.llm = llm or get_llm(temperature=0.0, max_tokens=512)
        self.name = AgentName.ORCHESTRATOR

    # ── Main entrypoint ─────────────────────────────────────────────────────

    def plan(self, state: AgentState) -> AgentState:
        """
        Analyse current state and decide the next action.

        Updates state.next_agent, state.reasoning_trace, and increments iteration.
        Returns the mutated state.
        """
        start = time.perf_counter()
        state.increment_iteration()

        log.info(
            "orchestrator_plan",
            session_id=state.session_id,
            iteration=state.iteration_count,
            current_input=state.current_input,   # redacted in production
        )

        # Guard: max iterations
        if state.is_exhausted():
            log.warning("max_iterations_reached", session_id=state.session_id)
            state.add_trace("ORC: Max iterations reached — forcing FINISH")
            state.next_agent = None
            state.flow_status = FlowStatus.FAILED
            state.final_response = (
                "I was unable to complete your request within the allowed steps. "
                "Please contact your healthcare provider directly."
            )
            AGENT_CALLS.labels(agent="orchestrator", status="timeout").inc()
            return state

        # Build context summary for the LLM
        context = self._build_context(state)

        try:
            import json
            response = self.llm.invoke([
                SystemMessage(content=ORCHESTRATOR_SYSTEM_PROMPT),
                HumanMessage(content=context),
            ])
            raw = response.content.strip()

            # Track token usage if available
            if hasattr(response, "usage_metadata") and response.usage_metadata:
                um = response.usage_metadata
                LLM_TOKENS_USED.labels(agent="orchestrator", token_type="input").inc(
                    getattr(um, "input_tokens", 0)
                )
                LLM_TOKENS_USED.labels(agent="orchestrator", token_type="output").inc(
                    getattr(um, "output_tokens", 0)
                )

            decision = extract_json(raw)
            state = self._apply_decision(state, decision)
            AGENT_CALLS.labels(agent="orchestrator", status="success").inc()

        except Exception as exc:
            log.error("orchestrator_error", error=str(exc), session_id=state.session_id)
            state.add_trace(f"ORC ERROR: {exc}")
            # Safe fallback: always start with triage
            state.next_agent = AgentName.TRIAGE
            AGENT_CALLS.labels(agent="orchestrator", status="error").inc()

        AGENT_LATENCY.labels(agent="orchestrator").observe(time.perf_counter() - start)
        return state

    def route(self, state_dict: dict) -> str:
        """
        LangGraph conditional-edge function.
        Returns the string name of the next node (or '__end__').
        """
        from src.agent_state import AgentState
        state = AgentState.model_validate(state_dict) if isinstance(state_dict, dict) else state_dict

        if state.flow_status == FlowStatus.FAILED:
            return "synthesizer"
        if state.next_agent is None:
            return "synthesizer"
        if state.requires_human_review and not state.human_approved:
            return "human_review"
        return state.next_agent.value if hasattr(state.next_agent, "value") else str(state.next_agent)

    # ── Helpers ─────────────────────────────────────────────────────────────

    def _build_context(self, state: AgentState) -> str:
        """Summarise the current pipeline state for the LLM."""
        triage_done   = state.triage.severity_score > 0
        research_done = bool(state.research.summary)
        critic_ok     = state.critic.approved
        appt_booked   = state.appointment.booked

        lines = [
            f"Patient message: {state.current_input}",
            f"Iteration: {state.iteration_count}/{state.max_iterations}",
            f"Triage completed: {triage_done}",
        ]
        if triage_done:
            lines.append(
                f"Triage result: severity={state.triage.severity_score}, "
                f"urgency={state.triage.urgency_level}"
            )
        lines += [
            f"Research completed: {research_done}",
            f"Critic approved: {critic_ok}",
            f"Appointment booked: {appt_booked}",
        ]
        if state.reasoning_trace:
            lines.append("Previous reasoning: " + "; ".join(state.reasoning_trace[-3:]))
        return "\n".join(lines)

    def _apply_decision(self, state: AgentState, decision: dict) -> AgentState:
        """Write the orchestrator's JSON decision back into state."""
        reasoning = decision.get("reasoning", "")
        next_raw   = decision.get("next_agent", "triage")
        satisfied  = decision.get("goal_satisfied", False)
        subtasks   = decision.get("subtasks", [])

        state.add_trace(f"ORC: {reasoning[:200]}")
        state.metadata["subtasks"] = subtasks

        if satisfied or next_raw.upper() == "FINISH":
            state.next_agent = None
            log.info("orchestrator_goal_satisfied", session_id=state.session_id)
        else:
            try:
                state.next_agent = AgentName(next_raw.lower())
            except ValueError:
                log.warning("unknown_next_agent", value=next_raw)
                state.next_agent = AgentName.TRIAGE   # safe default

        return state

"""
TriageAgent
-----------
Assesses symptom severity using the clinical ABCDE framework:
  A — Airway          (Is the airway clear?)
  B — Breathing       (Is breathing adequate?)
  C — Circulation     (Is circulation maintained?)
  D — Disability      (Neurological status)
  E — Exposure        (Any other visible issues)

Outputs a TriageResult with severity_score (0-10) and urgency_level.

Tools used:
  - symptom_lookup(symptom) → severity hint per symptom
  - severity_scale(symptoms) → aggregate across all reported symptoms
"""

from __future__ import annotations

import json
import time

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from tenacity import retry, stop_after_attempt, wait_exponential

from src.agent_state import AgentName, AgentState, TriageResult, UrgencyLevel
from src.config import settings
from src.observability.logging import get_logger
from src.observability.metrics import AGENT_CALLS, AGENT_LATENCY, LLM_TOKENS_USED
from src.tools.clinical_tools import severity_scale, symptom_lookup

log = get_logger(__name__)

TRIAGE_SYSTEM_PROMPT = """You are an expert clinical triage nurse AI. Assess the patient's symptoms
using the ABCDE framework (Airway, Breathing, Circulation, Disability, Exposure).

You will be given:
- The patient's reported symptoms/message
- Pre-computed severity hints from a symptom database

Your job: produce a structured triage assessment.

Output a JSON object with EXACTLY these keys:
{
  "severity_score": <integer 1-10, where 10 is life-threatening>,
  "urgency_level": <"emergency"|"urgent"|"routine">,
  "primary_concern": "<the most critical symptom or condition>",
  "abcde_assessment": {
    "airway": "<clear|compromised|unknown>",
    "breathing": "<normal|laboured|absent|unknown>",
    "circulation": "<normal|impaired|absent|unknown>",
    "disability": "<alert|confused|unresponsive|unknown>",
    "exposure": "<description of any visible injuries or conditions>"
  },
  "reasoning": "<your clinical reasoning in 2-3 sentences>"
}

CRITICAL: Respond ONLY with valid JSON — no markdown, no prose outside the JSON.
IMPORTANT: You are NOT diagnosing. You are triaging. Use conservative (higher) severity estimates when uncertain."""


class TriageAgent:
    """Clinical triage assessment using ABCDE framework + LLM reasoning."""

    def __init__(self, llm: ChatAnthropic | None = None) -> None:
        self.llm = llm or ChatAnthropic(
            model=settings.llm_model,
            max_tokens=512,
            temperature=0.0,
            anthropic_api_key=settings.anthropic_api_key,
        )
        self.name = AgentName.TRIAGE

    # ── Main entrypoint ─────────────────────────────────────────────────────

    def assess(self, state: AgentState) -> AgentState:
        """
        Run triage assessment on state.current_input.
        Populates state.triage with a TriageResult.
        """
        start = time.perf_counter()
        log.info("triage_assess_start", session_id=state.session_id)
        state.add_trace("TRIAGE: Starting ABCDE assessment")

        try:
            # 1. Extract keywords and get tool-based severity hints
            hints = self._get_severity_hints(state.current_input)
            state.add_trace(f"TRIAGE: Tool severity hints — max_score={hints['max_score']}, urgency={hints['urgency_level']}")

            # 2. LLM-based ABCDE assessment
            triage_result = self._llm_assess(state.current_input, hints)

            # 3. Apply conservative rule: tool hint overrides LLM if higher
            if hints["max_score"] > triage_result.severity_score:
                state.add_trace(
                    f"TRIAGE: Tool score ({hints['max_score']}) > LLM score ({triage_result.severity_score}) — using tool score"
                )
                triage_result.severity_score = hints["max_score"]
                triage_result.urgency_level = UrgencyLevel(hints["urgency_level"])

            state.triage = triage_result
            state.add_message("agent", f"Triage complete: {triage_result.urgency_level} (severity {triage_result.severity_score}/10)", AgentName.TRIAGE)
            state.add_trace(f"TRIAGE: Done — severity={triage_result.severity_score}, urgency={triage_result.urgency_level}")

            AGENT_CALLS.labels(agent="triage", status="success").inc()

        except Exception as exc:
            log.error("triage_error", error=str(exc), session_id=state.session_id)
            state.triage = TriageResult(
                severity_score=5,
                urgency_level=UrgencyLevel.URGENT,
                primary_concern="Assessment failed — defaulting to urgent",
                reasoning=f"Error during assessment: {exc}",
            )
            state.add_trace(f"TRIAGE ERROR: {exc} — defaulted to urgent/5")
            AGENT_CALLS.labels(agent="triage", status="error").inc()

        AGENT_LATENCY.labels(agent="triage").observe(time.perf_counter() - start)
        return state

    # ── Helpers ─────────────────────────────────────────────────────────────

    def _get_severity_hints(self, text: str) -> dict:
        """Extract symptom keywords from text and run severity_scale tool."""
        # Naive keyword extraction — sufficient for triage hints
        known_symptoms = [
            "chest pain", "breathing", "bleeding", "unconscious", "seizure",
            "stroke", "fever", "headache", "nausea", "vomiting", "dizziness",
            "abdominal pain", "rash", "sore throat", "cough", "confusion",
            "fainting", "broken bone", "anaphylaxis",
        ]
        found = [s for s in known_symptoms if s in text.lower()]
        if not found:
            found = [text[:50]]   # pass raw text as a single "symptom"
        return severity_scale(found)

    @retry(
        stop=stop_after_attempt(settings.agent_retry_attempts),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        reraise=True,
    )
    def _llm_assess(self, patient_message: str, hints: dict) -> TriageResult:
        """Call LLM with retry/backoff. Returns a validated TriageResult."""
        prompt = (
            f"Patient message: {patient_message}\n\n"
            f"Symptom database hints: {json.dumps(hints, indent=2)}\n\n"
            "Perform a full ABCDE triage assessment and return JSON."
        )
        response = self.llm.invoke([
            SystemMessage(content=TRIAGE_SYSTEM_PROMPT),
            HumanMessage(content=prompt),
        ])

        if hasattr(response, "usage_metadata") and response.usage_metadata:
            um = response.usage_metadata
            LLM_TOKENS_USED.labels(agent="triage", token_type="input").inc(getattr(um, "input_tokens", 0))
            LLM_TOKENS_USED.labels(agent="triage", token_type="output").inc(getattr(um, "output_tokens", 0))

        raw = response.content.strip()
        data = json.loads(raw)

        return TriageResult(
            severity_score=int(data.get("severity_score", 5)),
            urgency_level=UrgencyLevel(data.get("urgency_level", "urgent")),
            primary_concern=data.get("primary_concern", ""),
            abcde_assessment=data.get("abcde_assessment", {}),
            reasoning=data.get("reasoning", ""),
        )

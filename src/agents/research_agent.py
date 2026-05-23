"""
ResearchAgent
-------------
Retrieves relevant clinical guidelines and evidence-based recommendations
from the local Chroma vector store, then summarises them for the patient's
specific situation.

Tools:
  - vector_search(query, k) → list of Document chunks
  - Falls back to built-in heuristics if vector store is empty/unavailable
"""

from __future__ import annotations

import json
import time
from src.utils import extract_json
from functools import lru_cache

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from tenacity import retry, stop_after_attempt, wait_exponential

from src.agent_state import AgentName, AgentState, ResearchResult
from src.config import settings
from src.llm.provider import get_llm
from src.observability.logging import get_logger
from src.observability.metrics import AGENT_CALLS, AGENT_LATENCY, LLM_TOKENS_USED

log = get_logger(__name__)

RESEARCH_SYSTEM_PROMPT = """You are a medical research assistant AI. You will receive:
1. A patient's triage summary (urgency + primary concern)
2. Retrieved clinical guideline excerpts from a medical knowledge base

Your job: synthesise the guidelines into a clear, actionable recommendation summary.

Output a JSON object with EXACTLY these keys:
{
  "summary": "<2-4 sentence recommendation tailored to this patient's urgency level>",
  "guidelines_applied": ["<guideline name 1>", "<guideline name 2>"],
  "confidence_score": <float 0.0-1.0, how well the retrieved documents match this case>,
  "key_actions": ["<action 1>", "<action 2>", "<action 3>"]
}

CRITICAL: Your response must start with { and end with }. 
Output raw JSON only. No greetings, no explanations, no markdown, no code blocks.
First character of your response must be {
IMPORTANT: This is informational only — not a diagnosis or prescription."""

# Built-in fallback guidelines (used when vector store is empty)
FALLBACK_GUIDELINES: dict[str, dict] = {
    "emergency": {
        "summary": "Based on emergency triage protocols, immediate medical attention is required. "
                   "Call emergency services (911) or proceed to the nearest emergency department.",
        "guidelines": ["WHO Emergency Triage Guidelines", "ATLS Protocol"],
        "key_actions": ["Call 911 immediately", "Do not drive yourself", "Stay calm and keep patient still"],
    },
    "urgent": {
        "summary": "Your symptoms require prompt medical evaluation within the next few hours. "
                   "Visit an urgent care center or contact your physician immediately.",
        "guidelines": ["Primary Care Urgent Triage Protocol"],
        "key_actions": ["Visit urgent care within 2-4 hours", "Monitor symptoms closely", "Avoid strenuous activity"],
    },
    "routine": {
        "summary": "Your symptoms can be managed with a scheduled appointment. "
                   "Monitor for any worsening and contact your provider if symptoms escalate.",
        "guidelines": ["Primary Care Scheduling Guidelines"],
        "key_actions": ["Schedule appointment within 1 week", "Rest and stay hydrated", "Take OTC medication if appropriate"],
    },
}


class ResearchAgent:
    """Retrieves and summarises clinical guidelines relevant to the triage outcome."""

    def __init__(self, llm: BaseChatModel | None = None, vector_store=None) -> None:
        self.llm = llm or get_llm(temperature=0.1, max_tokens=768)
        self.vector_store = vector_store
        self.name = AgentName.RESEARCH

    # ── Main entrypoint ─────────────────────────────────────────────────────

    def retrieve(self, state: AgentState) -> AgentState:
        """
        Retrieve guidelines for the current triage result and summarise them.
        Populates state.research with a ResearchResult.
        """
        start = time.perf_counter()
        log.info(
            "research_retrieve_start",
            session_id=state.session_id,
            urgency=state.triage.urgency_level,
            severity=state.triage.severity_score,
        )
        state.add_trace(
            f"RESEARCH: Retrieving guidelines for urgency={state.triage.urgency_level}, "
            f"concern='{state.triage.primary_concern}'"
        )

        try:
            docs = self._retrieve_documents(state)
            result = self._summarise(state, docs)
            state.research = result
            state.add_message(
                "agent",
                f"Research complete: {len(result.sources)} sources, confidence={result.confidence_score:.2f}",
                AgentName.RESEARCH,
            )
            state.add_trace(f"RESEARCH: Done — confidence={result.confidence_score:.2f}, sources={len(result.sources)}")
            AGENT_CALLS.labels(agent="research", status="success").inc()

        except Exception as exc:
            log.error("research_error", error=str(exc), session_id=state.session_id)
            # Fallback to built-in guidelines
            urgency = str(state.triage.urgency_level).replace("UrgencyLevel.", "")
            fb = FALLBACK_GUIDELINES.get(urgency, FALLBACK_GUIDELINES["routine"])
            state.research = ResearchResult(
                summary=fb["summary"],
                guidelines_applied=fb["guidelines"],
                confidence_score=0.5,
                sources=[{"title": g, "type": "built-in"} for g in fb["guidelines"]],
            )
            state.add_trace(f"RESEARCH ERROR: {exc} — using fallback guidelines")
            AGENT_CALLS.labels(agent="research", status="error").inc()

        AGENT_LATENCY.labels(agent="research").observe(time.perf_counter() - start)
        return state

    # ── Helpers ─────────────────────────────────────────────────────────────

    def _retrieve_documents(self, state: AgentState) -> list[dict]:
        """Query vector store; fall back to empty list if unavailable."""
        query = (
            f"{state.triage.urgency_level} {state.triage.primary_concern} "
            f"{state.current_input[:100]}"
        )

        if self.vector_store is None:
            log.debug("research_no_vector_store", session_id=state.session_id)
            return []

        try:
            results = self.vector_store.similarity_search(query, k=5)
            return [
                {
                    "content": doc.page_content[:500],
                    "title": doc.metadata.get("title", "Clinical Guideline"),
                    "source": doc.metadata.get("source", "Medical Knowledge Base"),
                }
                for doc in results
            ]
        except Exception as exc:
            log.warning("vector_search_failed", error=str(exc))
            return []

    @retry(
        stop=stop_after_attempt(settings.agent_retry_attempts),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        reraise=True,
    )
    def _summarise(self, state: AgentState, docs: list[dict]) -> ResearchResult:
        """Use LLM to synthesise retrieved docs into actionable guidance."""
        urgency = str(state.triage.urgency_level)
        concern = state.triage.primary_concern
        severity = state.triage.severity_score

        if docs:
            docs_text = "\n\n".join(
                f"[{i+1}] {d['title']}: {d['content']}" for i, d in enumerate(docs)
            )
        else:
            # No vector store docs — instruct LLM to use general medical knowledge
            urgency_key = urgency.lower().split(".")[-1]   # handle enum string
            fb = FALLBACK_GUIDELINES.get(urgency_key, FALLBACK_GUIDELINES["routine"])
            return ResearchResult(
                summary=fb["summary"],
                guidelines_applied=fb["guidelines"],
                confidence_score=0.6,
                sources=[{"title": g, "type": "built-in"} for g in fb["guidelines"]],
            )

        prompt = (
            f"Patient triage summary:\n"
            f"  Urgency level: {urgency}\n"
            f"  Primary concern: {concern}\n"
            f"  Severity score: {severity}/10\n\n"
            f"Retrieved clinical guidelines:\n{docs_text}\n\n"
            "Synthesise these guidelines into a recommendation JSON."
        )

        response = self.llm.invoke([
            SystemMessage(content=RESEARCH_SYSTEM_PROMPT),
            HumanMessage(content=prompt),
        ])

        if hasattr(response, "usage_metadata") and response.usage_metadata:
            um = response.usage_metadata
            LLM_TOKENS_USED.labels(agent="research", token_type="input").inc(getattr(um, "input_tokens", 0))
            LLM_TOKENS_USED.labels(agent="research", token_type="output").inc(getattr(um, "output_tokens", 0))

        data = extract_json(response.content.strip())
        return ResearchResult(
            summary=data.get("summary", ""),
            guidelines_applied=data.get("guidelines_applied", []),
            confidence_score=float(data.get("confidence_score", 0.7)),
            sources=[{"title": g, "type": "retrieved"} for g in data.get("guidelines_applied", [])],
        )

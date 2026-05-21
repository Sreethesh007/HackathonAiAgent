"""
HealthcareTriageGraph
----------------------
The LangGraph StateGraph that connects all agents into a directed pipeline.

Flow:
  START
    └─► orchestrator (plan + route)
          ├─► triage → research → critic
          │     ├─► [approved]        → scheduler? → synthesizer → END
          │     ├─► [human review]    → human_review → synthesizer → END
          │     └─► [needs retry]     → orchestrator (loop, max iterations guarded)
          └─► synthesizer (on failure/exhaustion) → END

Checkpointing: MemorySaver keeps conversation state across API calls
               (enables multi-turn sessions without re-running the whole graph).

HITL: interrupt_before=["human_review"] pauses the graph so an external
      API call can inject the reviewer's decision before resuming.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from src.agent_state import AgentName, AgentState, FlowStatus
from src.agents.orchestrator import OrchestratorAgent
from src.agents.research_agent import ResearchAgent
from src.agents.scheduler_critic_agents import CriticAgent, SchedulerAgent
from src.agents.synthesizer import HumanReviewNode, Synthesizer
from src.agents.triage_agent import TriageAgent
from src.config import settings
from src.observability.logging import get_logger

log = get_logger(__name__)


# ── LangGraph requires dict-based state reducers ────────────────────────────
# We use a thin adapter: convert AgentState ↔ dict at each node boundary.

def _state_to_dict(state: AgentState) -> dict:
    return state.model_dump(mode="json")

def _dict_to_state(d: dict) -> AgentState:
    return AgentState.model_validate(d)


class HealthcareTriageGraph:
    """
    Builds and compiles the LangGraph pipeline.

    Usage:
        graph = HealthcareTriageGraph()
        result = await graph.run(patient_id="P001", message="chest pain")
    """

    def __init__(
        self,
        orchestrator: OrchestratorAgent | None = None,
        triage: TriageAgent | None = None,
        research: ResearchAgent | None = None,
        scheduler: SchedulerAgent | None = None,
        critic: CriticAgent | None = None,
        synthesizer: Synthesizer | None = None,
    ) -> None:
        self.orchestrator  = orchestrator or OrchestratorAgent()
        self.triage        = triage       or TriageAgent()
        self.research      = research     or ResearchAgent()
        self.scheduler     = scheduler    or SchedulerAgent()
        self.critic        = critic       or CriticAgent()
        self.synthesizer   = synthesizer  or Synthesizer()
        self.human_review  = HumanReviewNode()
        self.checkpointer  = MemorySaver()
        self._graph        = self._build()

    # ── Node wrappers ────────────────────────────────────────────────────────
    # LangGraph nodes receive and return dict[str, Any].
    # We convert to/from AgentState for type safety inside each agent.

    def _node_orchestrator(self, state_dict: dict) -> dict:
        state = _dict_to_state(state_dict)
        state = self.orchestrator.plan(state)
        return _state_to_dict(state)

    def _node_triage(self, state_dict: dict) -> dict:
        state = _dict_to_state(state_dict)
        state = self.triage.assess(state)
        return _state_to_dict(state)

    def _node_research(self, state_dict: dict) -> dict:
        state = _dict_to_state(state_dict)
        state = self.research.retrieve(state)
        return _state_to_dict(state)

    def _node_scheduler(self, state_dict: dict) -> dict:
        state = _dict_to_state(state_dict)
        state = self.scheduler.book(state)
        return _state_to_dict(state)

    def _node_critic(self, state_dict: dict) -> dict:
        state = _dict_to_state(state_dict)
        state = self.critic.review(state)
        return _state_to_dict(state)

    def _node_human_review(self, state_dict: dict) -> dict:
        state = _dict_to_state(state_dict)
        state = self.human_review.pause(state)
        return _state_to_dict(state)

    def _node_synthesizer(self, state_dict: dict) -> dict:
        state = _dict_to_state(state_dict)
        state = self.synthesizer.synthesize(state)
        return _state_to_dict(state)

    # ── Conditional routing functions ────────────────────────────────────────

    def _route_orchestrator(self, state_dict: dict) -> str:
        """After orchestrator.plan(), decide which node to visit next."""
        state = _dict_to_state(state_dict)

        if state.flow_status == FlowStatus.FAILED:
            return "synthesizer"
        if state.is_exhausted():
            return "synthesizer"
        if state.next_agent == AgentName.TRIAGE:
            return "triage"
        if state.next_agent == AgentName.RESEARCH:
            return "research"
        if state.next_agent == AgentName.SCHEDULER:
            return "scheduler"
        if state.next_agent is None:
            return "synthesizer"
        return "triage"   # safe default

    def _route_critic(self, state_dict: dict) -> str:
        """After critic.review(), decide where to go."""
        state = _dict_to_state(state_dict)

        if state.requires_human_review:
            return "human_review"
        if state.critic.approved:
            # Only book appointment for non-emergency cases
            urgency = str(state.triage.urgency_level).lower()
            if "emergency" not in urgency and not state.appointment.booked:
                return "scheduler"
            return "synthesizer"
        # Not approved, not human review → retry via orchestrator (if iterations allow)
        if not state.is_exhausted():
            return "orchestrator"
        return "synthesizer"

    # ── Graph builder ────────────────────────────────────────────────────────

    def _build(self):
        g = StateGraph(dict)   # LangGraph uses dict as the native state type

        # Register nodes
        g.add_node("orchestrator",  self._node_orchestrator)
        g.add_node("triage",        self._node_triage)
        g.add_node("research",      self._node_research)
        g.add_node("scheduler",     self._node_scheduler)
        g.add_node("critic",        self._node_critic)
        g.add_node("human_review",  self._node_human_review)
        g.add_node("synthesizer",   self._node_synthesizer)

        # Entry
        g.add_edge(START, "orchestrator")

        # Orchestrator → conditional
        g.add_conditional_edges("orchestrator", self._route_orchestrator, {
            "triage":      "triage",
            "research":    "research",
            "scheduler":   "scheduler",
            "synthesizer": "synthesizer",
        })

        # Triage always feeds into research
        g.add_edge("triage", "research")

        # Research always feeds into critic
        g.add_edge("research", "critic")

        # Critic → conditional
        g.add_conditional_edges("critic", self._route_critic, {
            "human_review": "human_review",
            "scheduler":    "scheduler",
            "synthesizer":  "synthesizer",
            "orchestrator": "orchestrator",
        })

        # After booking, synthesise
        g.add_edge("scheduler", "synthesizer")

        # Human review → synthesizer (graph resumes here after HITL approval)
        g.add_edge("human_review", "synthesizer")

        # Terminal
        g.add_edge("synthesizer", END)

        return g.compile(
            checkpointer=self.checkpointer,
            interrupt_before=["human_review"],   # HITL pause point
        )

    # ── Public API ───────────────────────────────────────────────────────────

    def run(
        self,
        patient_id: str,
        message: str,
        session_id: str | None = None,
        max_iterations: int | None = None,
    ) -> AgentState:
        """
        Run a full triage flow for one patient message.

        Args:
            patient_id:     Unique patient identifier (⚠ PII)
            message:        Patient's natural-language message
            session_id:     Reuse an existing session for multi-turn conversations
            max_iterations: Override the default max iterations

        Returns:
            Final AgentState with populated triage, research, appointment, and final_response.
        """
        import uuid

        initial_state = AgentState(
            patient_id=patient_id,
            current_input=message,
            max_iterations=max_iterations or settings.max_agent_iterations,
        )
        if session_id:
            initial_state.session_id = session_id

        initial_state.add_message("user", message)
        log.info(
            "pipeline_start",
            session_id=initial_state.session_id,
            patient_id=patient_id,   # redacted in production
        )

        config = {"configurable": {"thread_id": initial_state.session_id}}
        result_dict = self._graph.invoke(_state_to_dict(initial_state), config=config)
        return _dict_to_state(result_dict)

    def resume(self, session_id: str, human_approved: bool) -> AgentState:
        """
        Resume a HITL-paused session after human reviewer decision.

        Args:
            session_id:     The paused session's ID
            human_approved: True = approve and continue, False = reject
        """
        config = {"configurable": {"thread_id": session_id}}

        # Fetch current checkpoint state
        current = self._graph.get_state(config)
        if current is None:
            raise ValueError(f"No paused session found for session_id={session_id}")

        # Inject human decision into state
        state = _dict_to_state(current.values)
        state = self.human_review.resume(state, human_approved)

        # Update checkpoint and resume graph
        self._graph.update_state(config, _state_to_dict(state))
        result_dict = self._graph.invoke(None, config=config)   # None = resume from checkpoint
        return _dict_to_state(result_dict)

    def export_mermaid(self, output_path: str = "docs/graph.md") -> None:
        """Export the graph as a Mermaid diagram to docs/graph.md."""
        try:
            mermaid = self._graph.get_graph().draw_mermaid()
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            Path(output_path).write_text(f"```mermaid\n{mermaid}\n```\n")
            log.info("graph_exported", path=output_path)
        except Exception as exc:
            log.warning("graph_export_failed", error=str(exc))

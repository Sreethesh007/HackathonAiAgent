"""
Full test suite — unit + integration + edge cases.

Run with:
    pytest tests/ -v --tb=short

Coverage targets:
    src/agent_state.py       → 100%
    src/tools/clinical_tools → 95%+
    src/agents/*             → 85%+
    src/graph/pipeline.py    → 80%+
    src/api/*                → 80%+
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def base_state():
    from src.agent_state import AgentState
    return AgentState(
        patient_id="TEST-001",
        current_input="I have a headache and slight nausea",
    )


@pytest.fixture
def emergency_state():
    from src.agent_state import AgentState, TriageResult, UrgencyLevel
    state = AgentState(patient_id="TEST-EMG", current_input="severe chest pain radiating to arm")
    state.triage = TriageResult(severity_score=9, urgency_level=UrgencyLevel.EMERGENCY,
                                primary_concern="chest pain", reasoning="High severity")
    return state


@pytest.fixture
def mock_llm_factory():
    """Returns a factory that creates a MagicMock LLM with a given response text."""
    def factory(response_text: str):
        llm = MagicMock()
        mock_response = MagicMock()
        mock_response.content = response_text
        mock_response.usage_metadata = None
        llm.invoke.return_value = mock_response
        return llm
    return factory


# ─────────────────────────────────────────────────────────────────────────────
# Stage 1 — AgentState
# ─────────────────────────────────────────────────────────────────────────────

class TestAgentState:
    def test_default_instantiation(self):
        from src.agent_state import AgentState
        state = AgentState(patient_id="P001", current_input="test")
        assert state.schema_version == "1.0.0"
        assert state.session_id  # auto-generated UUID
        assert state.iteration_count == 0
        assert state.flow_status.value == "running"

    def test_add_message(self, base_state):
        from src.agent_state import AgentName
        base_state.add_message("user", "Hello", AgentName.ORCHESTRATOR)
        assert len(base_state.messages) == 1
        assert base_state.messages[0].content == "Hello"

    def test_add_trace(self, base_state):
        base_state.add_trace("Test step")
        assert any("Test step" in t for t in base_state.reasoning_trace)

    def test_increment_iteration(self, base_state):
        base_state.increment_iteration()
        assert base_state.iteration_count == 1

    def test_is_exhausted_false(self, base_state):
        base_state.iteration_count = 5
        base_state.max_iterations = 10
        assert not base_state.is_exhausted()

    def test_is_exhausted_true(self, base_state):
        base_state.iteration_count = 10
        base_state.max_iterations = 10
        assert base_state.is_exhausted()

    def test_severity_score_clamped(self):
        from src.agent_state import TriageResult
        r = TriageResult(severity_score=15)   # clamped before pydantic validates
        assert r.severity_score == 10
        r2 = TriageResult(severity_score=-3)  # clamped before pydantic validates
        assert r2.severity_score == 0

    def test_safe_log_dict_redacts_pii(self, base_state):
        base_state.patient_id = "REAL-PATIENT-ID"
        base_state.current_input = "My private symptoms"
        safe = base_state.safe_log_dict()
        assert "REAL-PATIENT-ID" not in str(safe["patient_id"])
        assert safe["current_input"] == "<redacted>"

    def test_json_serialization(self, base_state):
        d = base_state.model_dump(mode="json")
        assert isinstance(d, dict)
        assert "session_id" in d
        restored = type(base_state).model_validate(d)
        assert restored.session_id == base_state.session_id


# ─────────────────────────────────────────────────────────────────────────────
# Stage 2 — Clinical Tools
# ─────────────────────────────────────────────────────────────────────────────

class TestClinicalTools:
    def test_symptom_lookup_known(self):
        from src.tools.clinical_tools import symptom_lookup
        result = symptom_lookup("chest pain")
        assert result["severity_score"] == 9
        assert result["urgency_hint"] == "emergency"

    def test_symptom_lookup_unknown(self):
        from src.tools.clinical_tools import symptom_lookup
        result = symptom_lookup("xyzzy_nonexistent_symptom_xyz")
        assert result["severity_score"] == 0
        assert result["urgency_hint"] == "unknown"

    def test_symptom_lookup_partial_match(self):
        from src.tools.clinical_tools import symptom_lookup
        result = symptom_lookup("I have a bad headache")
        assert result["severity_score"] > 0

    def test_severity_scale_empty(self):
        from src.tools.clinical_tools import severity_scale
        result = severity_scale([])
        assert result["max_score"] == 0
        assert result["urgency_level"] == "unknown"

    def test_severity_scale_mixed(self):
        from src.tools.clinical_tools import severity_scale
        result = severity_scale(["headache", "chest pain", "sore throat"])
        assert result["max_score"] == 9
        assert result["urgency_level"] == "emergency"

    def test_check_availability_returns_slots(self):
        from src.tools.clinical_tools import check_availability
        slots = check_availability("next week", urgency="routine")
        assert len(slots) >= 1
        assert "slot_id" in slots[0]
        assert "datetime_iso" in slots[0]

    def test_check_availability_emergency_earlier(self):
        from src.tools.clinical_tools import check_availability
        from datetime import datetime
        emergency_slots = check_availability("asap", urgency="emergency")
        routine_slots   = check_availability("next week", urgency="routine")
        # Emergency slots should be earlier than routine
        emg_dt = datetime.fromisoformat(emergency_slots[0]["datetime_iso"])
        rtn_dt = datetime.fromisoformat(routine_slots[0]["datetime_iso"])
        assert emg_dt <= rtn_dt

    def test_book_appointment_returns_id(self):
        from src.tools.clinical_tools import book_appointment
        result = book_appointment("SLOT-001", "P12345", "headache")
        assert result["appointment_id"].startswith("APT-")
        assert result["status"] == "confirmed"


# ─────────────────────────────────────────────────────────────────────────────
# Stage 3 — Triage Agent
# ─────────────────────────────────────────────────────────────────────────────

class TestTriageAgent:
    def test_triage_success(self, base_state, mock_llm_factory):
        from src.agents.triage_agent import TriageAgent
        from src.agent_state import UrgencyLevel

        llm_response = json.dumps({
            "severity_score": 4,
            "urgency_level": "routine",
            "primary_concern": "headache with nausea",
            "abcde_assessment": {
                "airway": "clear", "breathing": "normal",
                "circulation": "normal", "disability": "alert", "exposure": "none"
            },
            "reasoning": "Mild symptoms, no red flags."
        })
        agent = TriageAgent(llm=mock_llm_factory(llm_response))
        result_state = agent.assess(base_state)

        assert result_state.triage.severity_score >= 1
        assert result_state.triage.urgency_level in [UrgencyLevel.ROUTINE, UrgencyLevel.URGENT, UrgencyLevel.EMERGENCY]

    def test_triage_emergency_override(self, mock_llm_factory):
        """Tool-based score must override LLM if tool gives higher severity."""
        from src.agents.triage_agent import TriageAgent
        from src.agent_state import AgentState, UrgencyLevel

        # LLM says "routine" but symptom is "chest pain" (score=9)
        llm_response = json.dumps({
            "severity_score": 2,
            "urgency_level": "routine",
            "primary_concern": "chest pain",
            "abcde_assessment": {},
            "reasoning": "Seems mild."
        })
        agent = TriageAgent(llm=mock_llm_factory(llm_response))
        state = AgentState(patient_id="P001", current_input="I have chest pain")
        result = agent.assess(state)

        # Tool score (9) should override LLM's 2
        assert result.triage.severity_score == 9
        assert result.triage.urgency_level == UrgencyLevel.EMERGENCY

    def test_triage_llm_failure_fallback(self, base_state, mock_llm_factory):
        """When LLM fails, triage should fallback to severity=5/urgent."""
        from src.agents.triage_agent import TriageAgent
        from src.agent_state import UrgencyLevel

        llm = MagicMock()
        llm.invoke.side_effect = Exception("LLM timeout")
        agent = TriageAgent(llm=llm)
        result = agent.assess(base_state)

        assert result.triage.severity_score == 5
        assert result.triage.urgency_level == UrgencyLevel.URGENT

    @pytest.mark.parametrize("symptom,min_score", [
        ("cardiac arrest", 10),
        ("stroke", 10),
        ("high fever", 6),
        ("sore throat", 1),
    ])
    def test_severity_parametrize(self, symptom, min_score, mock_llm_factory):
        from src.tools.clinical_tools import symptom_lookup
        result = symptom_lookup(symptom)
        assert result["severity_score"] >= min_score


# ─────────────────────────────────────────────────────────────────────────────
# Stage 4 — Research Agent
# ─────────────────────────────────────────────────────────────────────────────

class TestResearchAgent:
    def test_research_fallback_no_vector_store(self, emergency_state):
        """Without a vector store, research should use built-in fallback guidelines."""
        from src.agents.research_agent import ResearchAgent
        # Inject a mock LLM so the test doesn't call get_llm() (which needs a real API key)
        mock_llm = MagicMock()
        agent = ResearchAgent(llm=mock_llm, vector_store=None)
        result = agent.retrieve(emergency_state)
        # Fallback path returns built-in guidelines without calling LLM
        assert result.research.summary != ""
        assert result.research.confidence_score > 0

    def test_research_with_mock_vector_store(self, emergency_state, mock_llm_factory):
        from src.agents.research_agent import ResearchAgent
        from langchain_core.documents import Document

        mock_vs = MagicMock()
        mock_vs.similarity_search.return_value = [
            Document(page_content="Emergency cardiac protocol...", metadata={"title": "AHA Guidelines"}),
        ]
        llm_response = json.dumps({
            "summary": "Call emergency services immediately.",
            "guidelines_applied": ["AHA Guidelines"],
            "confidence_score": 0.9,
            "key_actions": ["Call 911"],
        })
        agent = ResearchAgent(llm=mock_llm_factory(llm_response), vector_store=mock_vs)
        result = agent.retrieve(emergency_state)

        assert result.research.confidence_score == 0.9
        assert "AHA Guidelines" in result.research.guidelines_applied


# ─────────────────────────────────────────────────────────────────────────────
# Stage 5 — Orchestrator Agent
# ─────────────────────────────────────────────────────────────────────────────

class TestOrchestratorAgent:
    def test_routes_to_triage_first(self, base_state, mock_llm_factory):
        from src.agents.orchestrator import OrchestratorAgent
        from src.agent_state import AgentName

        llm_response = json.dumps({
            "reasoning": "New patient message, must triage first.",
            "subtasks": ["assess_urgency"],
            "next_agent": "triage",
            "goal_satisfied": False,
        })
        agent = OrchestratorAgent(llm=mock_llm_factory(llm_response))
        result = agent.plan(base_state)
        assert result.next_agent == AgentName.TRIAGE

    def test_routes_to_finish_when_satisfied(self, base_state, mock_llm_factory):
        from src.agents.orchestrator import OrchestratorAgent

        llm_response = json.dumps({
            "reasoning": "All steps complete.",
            "subtasks": [],
            "next_agent": "FINISH",
            "goal_satisfied": True,
        })
        agent = OrchestratorAgent(llm=mock_llm_factory(llm_response))
        result = agent.plan(base_state)
        assert result.next_agent is None

    def test_max_iterations_guard(self, base_state, mock_llm_factory):
        from src.agents.orchestrator import OrchestratorAgent
        from src.agent_state import FlowStatus

        base_state.iteration_count = 9   # will hit 10 after increment
        base_state.max_iterations = 10
        agent = OrchestratorAgent(llm=mock_llm_factory("{}"))
        result = agent.plan(base_state)
        assert result.flow_status == FlowStatus.FAILED

    def test_route_function_failed_state(self, base_state):
        from src.agents.orchestrator import OrchestratorAgent
        from src.agent_state import FlowStatus
        base_state.flow_status = FlowStatus.FAILED
        agent = OrchestratorAgent(llm=MagicMock())
        assert agent.route(base_state.model_dump(mode="json")) == "synthesizer"


# ─────────────────────────────────────────────────────────────────────────────
# Stage 6 — Critic Agent
# ─────────────────────────────────────────────────────────────────────────────

class TestCriticAgent:
    def test_approves_good_state(self, emergency_state, mock_llm_factory):
        from src.agents.scheduler_critic_agents import CriticAgent
        from src.agent_state import ResearchResult

        emergency_state.research = ResearchResult(
            summary="Call 911.", confidence_score=0.9, guidelines_applied=["AHA"]
        )
        llm_response = json.dumps({
            "quality_score": 0.85,
            "approved": True,
            "issues_found": [],
            "feedback": "All good.",
            "requires_human_review": False,
        })
        agent = CriticAgent(llm=mock_llm_factory(llm_response))
        result = agent.review(emergency_state)
        assert result.critic.approved is True
        assert result.requires_human_review is False

    def test_flags_emergency_misclassified_as_routine(self, mock_llm_factory):
        from src.agents.scheduler_critic_agents import CriticAgent
        from src.agent_state import AgentState, TriageResult, UrgencyLevel, ResearchResult

        state = AgentState(patient_id="P001", current_input="severe chest pain")
        state.triage = TriageResult(severity_score=9, urgency_level=UrgencyLevel.ROUTINE,
                                    primary_concern="chest pain")
        state.research = ResearchResult(summary="See a doctor soon.", confidence_score=0.4)

        llm_response = json.dumps({
            "quality_score": 0.3,
            "approved": False,
            "issues_found": ["Severity 9 misclassified as routine"],
            "feedback": "Safety concern: high severity mismatch.",
            "requires_human_review": True,
        })
        agent = CriticAgent(llm=mock_llm_factory(llm_response))
        result = agent.review(state)
        assert result.critic.approved is False
        assert result.requires_human_review is True

    def test_critic_failure_forces_human_review(self, base_state):
        from src.agents.scheduler_critic_agents import CriticAgent
        llm = MagicMock()
        llm.invoke.side_effect = Exception("LLM error")
        agent = CriticAgent(llm=llm)
        result = agent.review(base_state)
        assert result.requires_human_review is True
        assert result.critic.approved is False


# ─────────────────────────────────────────────────────────────────────────────
# Stage 7 — Pipeline Integration (mocked LLM)
# ─────────────────────────────────────────────────────────────────────────────

class TestPipelineIntegration:
    def _make_pipeline(self, mock_llm_factory):
        """Build a pipeline where all agents use a mock LLM."""
        from src.graph.pipeline import HealthcareTriageGraph
        from src.agents.orchestrator import OrchestratorAgent
        from src.agents.triage_agent import TriageAgent
        from src.agents.research_agent import ResearchAgent
        from src.agents.scheduler_critic_agents import CriticAgent, SchedulerAgent
        from src.agents.synthesizer import Synthesizer

        orch_resp = json.dumps({"reasoning": "triage first", "subtasks": ["assess_urgency"],
                                "next_agent": "triage", "goal_satisfied": False})
        triage_resp = json.dumps({"severity_score": 3, "urgency_level": "routine",
                                  "primary_concern": "headache", "abcde_assessment": {},
                                  "reasoning": "Mild."})
        research_resp = json.dumps({"summary": "Rest and hydrate.", "guidelines_applied": ["PCG"],
                                    "confidence_score": 0.8, "key_actions": ["Rest"]})
        critic_resp = json.dumps({"quality_score": 0.85, "approved": True,
                                  "issues_found": [], "feedback": "Good.", "requires_human_review": False})
        scheduler_resp = json.dumps({"selected_slot_id": "SLOT-PLACEHOLDER",
                                     "reasoning": "First available.", "appointment_type": "in_person",
                                     "pre_appointment_advice": "Bring ID."})
        # Synthesizer gets a plain text response
        synth_llm = mock_llm_factory("Based on your symptoms, we recommend rest and scheduling a check-up. "
                                     "If symptoms worsen, seek emergency care immediately.")

        # For scheduler slot selection, we need to return a valid slot_id
        # We'll patch check_availability to return a predictable slot
        return HealthcareTriageGraph(
            orchestrator=OrchestratorAgent(llm=mock_llm_factory(orch_resp)),
            triage=TriageAgent(llm=mock_llm_factory(triage_resp)),
            research=ResearchAgent(llm=mock_llm_factory(research_resp), vector_store=None),
            scheduler=SchedulerAgent(llm=mock_llm_factory(scheduler_resp)),
            critic=CriticAgent(llm=mock_llm_factory(critic_resp)),
            synthesizer=Synthesizer(llm=synth_llm),
        )

    def test_happy_path_routine(self, mock_llm_factory):
        """End-to-end: routine patient message produces final response."""
        pipeline = self._make_pipeline(mock_llm_factory)
        state = pipeline.run(patient_id="P001", message="I have a mild headache")
        assert state.final_response != ""
        assert state.triage.severity_score >= 1

    def test_session_id_preserved(self, mock_llm_factory):
        """Session ID passed in is preserved in output state."""
        pipeline = self._make_pipeline(mock_llm_factory)
        sid = str(uuid.uuid4())
        state = pipeline.run(patient_id="P001", message="mild cough", session_id=sid)
        assert state.session_id == sid

    def test_max_iterations_terminates(self, mock_llm_factory):
        """Pipeline must terminate even if agents keep looping."""
        from src.graph.pipeline import HealthcareTriageGraph
        from src.agents.orchestrator import OrchestratorAgent
        from src.agents.triage_agent import TriageAgent
        from src.agents.research_agent import ResearchAgent
        from src.agents.scheduler_critic_agents import CriticAgent, SchedulerAgent
        from src.agents.synthesizer import Synthesizer

        # Orchestrator always says "keep going"
        loop_resp = json.dumps({"reasoning": "loop", "subtasks": [],
                                "next_agent": "triage", "goal_satisfied": False})
        triage_resp = json.dumps({"severity_score": 3, "urgency_level": "routine",
                                  "primary_concern": "test", "abcde_assessment": {}, "reasoning": "ok"})
        research_resp = json.dumps({"summary": "ok", "guidelines_applied": [],
                                    "confidence_score": 0.5, "key_actions": []})
        critic_resp = json.dumps({"quality_score": 0.5, "approved": False,
                                  "issues_found": ["retry"], "feedback": "retry", "requires_human_review": False})
        synth_resp = "Please contact your provider."

        pipeline = HealthcareTriageGraph(
            orchestrator=OrchestratorAgent(llm=mock_llm_factory(loop_resp)),
            triage=TriageAgent(llm=mock_llm_factory(triage_resp)),
            research=ResearchAgent(llm=mock_llm_factory(research_resp), vector_store=None),
            scheduler=SchedulerAgent(llm=mock_llm_factory("{}")),
            critic=CriticAgent(llm=mock_llm_factory(critic_resp)),
            synthesizer=Synthesizer(llm=mock_llm_factory(synth_resp)),
        )
        state = pipeline.run(patient_id="P001", message="test", max_iterations=3)
        # Must complete (not hang) and have a final response
        assert state.final_response != ""
        assert state.iteration_count <= 3 + 5   # some buffer for graph overhead


# ─────────────────────────────────────────────────────────────────────────────
# Stage 8 — Auth
# ─────────────────────────────────────────────────────────────────────────────

class TestAuth:
    def test_create_and_decode_token(self):
        from src.api.auth import create_access_token
        from jose import jwt
        from src.config import settings

        token = create_access_token("user123", role="admin")
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        assert payload["sub"] == "user123"
        assert payload["role"] == "admin"

    def test_expired_token_raises(self):
        from src.api.auth import create_access_token, get_current_user
        from src.config import settings
        from jose import jwt
        from datetime import datetime, timedelta

        # Manually create expired token
        payload = {"sub": "user", "role": "clinician", "exp": datetime.utcnow() - timedelta(seconds=1)}
        token = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)

        import asyncio
        from fastapi.security import HTTPAuthorizationCredentials
        creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        with pytest.raises(Exception):   # HTTPException 401
            asyncio.get_event_loop().run_until_complete(get_current_user(creds))

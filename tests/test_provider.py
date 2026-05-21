"""
Tests for the LLM provider factory and provider-switching logic.

All tests mock actual LLM calls — no API key or server required.
"""

from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import pytest


# ─────────────────────────────────────────────────────────────────────────────
# Provider factory tests
# ─────────────────────────────────────────────────────────────────────────────

class TestProviderFactory:

    def test_get_llm_anthropic(self):
        """get_llm() returns ChatAnthropic when provider=anthropic."""
        with patch.dict(os.environ, {"LLM_PROVIDER": "anthropic", "ANTHROPIC_API_KEY": "test-key"}):
            # Re-create settings with patched env
            from importlib import reload
            import src.config as cfg_mod
            reload(cfg_mod)
            import src.llm.provider as prov_mod
            reload(prov_mod)

            with patch("src.llm.provider._build_anthropic") as mock_build:
                mock_build.return_value = MagicMock()
                prov_mod.get_llm()
                mock_build.assert_called_once()

    def test_get_llm_llamacpp(self):
        """get_llm() returns ChatOpenAI (llama.cpp) when provider=llamacpp."""
        with patch.dict(os.environ, {
            "LLM_PROVIDER": "llamacpp",
            "LLAMACPP_BASE_URL": "http://localhost:8080",
            "ANTHROPIC_API_KEY": "",
        }):
            from importlib import reload
            import src.config as cfg_mod
            reload(cfg_mod)
            import src.llm.provider as prov_mod
            reload(prov_mod)

            with patch("src.llm.provider._build_llamacpp") as mock_build:
                mock_build.return_value = MagicMock()
                prov_mod.get_llm()
                mock_build.assert_called_once()

    def test_invalid_provider_raises(self):
        """get_llm() raises RuntimeError for unknown provider."""
        with patch.dict(os.environ, {"LLM_PROVIDER": "openai_gpt99"}):
            from importlib import reload
            import src.config as cfg_mod
            reload(cfg_mod)
            import src.llm.provider as prov_mod
            reload(prov_mod)

            with pytest.raises(RuntimeError, match="LLM_PROVIDER"):
                prov_mod.get_llm()

    def test_anthropic_missing_key_raises(self):
        """get_llm() raises RuntimeError when Anthropic key is missing."""
        with patch.dict(os.environ, {"LLM_PROVIDER": "anthropic", "ANTHROPIC_API_KEY": ""}):
            from importlib import reload
            import src.config as cfg_mod
            reload(cfg_mod)
            import src.llm.provider as prov_mod
            reload(prov_mod)

            with pytest.raises(RuntimeError, match="ANTHROPIC_API_KEY"):
                prov_mod.get_llm()

    def test_get_provider_info_anthropic(self):
        """get_provider_info() returns correct dict for Anthropic."""
        with patch.dict(os.environ, {
            "LLM_PROVIDER": "anthropic",
            "ANTHROPIC_API_KEY": "sk-test",
            "LLM_MODEL": "claude-sonnet-4-20250514",
        }):
            from importlib import reload
            import src.config as cfg_mod
            reload(cfg_mod)
            import src.llm.provider as prov_mod
            reload(prov_mod)

            info = prov_mod.get_provider_info()
            assert info["provider"] == "anthropic"
            assert "model" in info
            assert info["api_key_set"] is True

    def test_get_provider_info_llamacpp(self):
        """get_provider_info() returns correct dict for llama.cpp."""
        with patch.dict(os.environ, {
            "LLM_PROVIDER": "llamacpp",
            "LLAMACPP_BASE_URL": "http://localhost:8080",
            "LLAMACPP_MODEL": "llama-3.1-8b-instruct",
            "ANTHROPIC_API_KEY": "",
        }):
            from importlib import reload
            import src.config as cfg_mod
            reload(cfg_mod)
            import src.llm.provider as prov_mod
            reload(prov_mod)

            info = prov_mod.get_provider_info()
            assert info["provider"] == "llamacpp"
            assert info["base_url"] == "http://localhost:8080"
            assert "n_ctx" in info

    def test_check_provider_health_anthropic_failure(self):
        """check_provider_health() returns ok=False when provider is unreachable."""
        with patch.dict(os.environ, {"LLM_PROVIDER": "anthropic", "ANTHROPIC_API_KEY": "bad-key"}):
            from importlib import reload
            import src.config as cfg_mod
            reload(cfg_mod)
            import src.llm.provider as prov_mod
            reload(prov_mod)

            with patch("src.llm.provider.get_llm") as mock_get_llm:
                mock_llm = MagicMock()
                mock_llm.invoke.side_effect = Exception("Connection refused")
                mock_get_llm.return_value = mock_llm

                result = prov_mod.check_provider_health()
                assert result["ok"] is False
                assert result["error"] is not None
                assert "latency_ms" in result

    def test_check_provider_health_success(self):
        """check_provider_health() returns ok=True when provider responds."""
        with patch.dict(os.environ, {"LLM_PROVIDER": "anthropic", "ANTHROPIC_API_KEY": "test-key"}):
            from importlib import reload
            import src.config as cfg_mod
            reload(cfg_mod)
            import src.llm.provider as prov_mod
            reload(prov_mod)

            with patch("src.llm.provider.get_llm") as mock_get_llm:
                mock_llm = MagicMock()
                mock_llm.invoke.return_value = MagicMock(content="pong")
                mock_get_llm.return_value = mock_llm

                result = prov_mod.check_provider_health()
                assert result["ok"] is True
                assert result["error"] is None


# ─────────────────────────────────────────────────────────────────────────────
# Settings validation tests
# ─────────────────────────────────────────────────────────────────────────────

class TestSettingsValidation:

    def test_validate_anthropic_ok(self):
        with patch.dict(os.environ, {"LLM_PROVIDER": "anthropic", "ANTHROPIC_API_KEY": "sk-real"}):
            from importlib import reload
            import src.config as cfg_mod
            reload(cfg_mod)
            issues = cfg_mod.get_settings().validate_llm_config()
            assert issues == []

    def test_validate_anthropic_missing_key(self):
        with patch.dict(os.environ, {"LLM_PROVIDER": "anthropic", "ANTHROPIC_API_KEY": ""}):
            from importlib import reload
            import src.config as cfg_mod
            reload(cfg_mod)
            issues = cfg_mod.get_settings().validate_llm_config()
            assert any("ANTHROPIC_API_KEY" in i for i in issues)

    def test_validate_llamacpp_ok(self):
        with patch.dict(os.environ, {
            "LLM_PROVIDER": "llamacpp",
            "LLAMACPP_BASE_URL": "http://localhost:8080",
            "ANTHROPIC_API_KEY": "",
        }):
            from importlib import reload
            import src.config as cfg_mod
            reload(cfg_mod)
            issues = cfg_mod.get_settings().validate_llm_config()
            assert issues == []

    def test_validate_unknown_provider(self):
        with patch.dict(os.environ, {"LLM_PROVIDER": "gpt5_turbo"}):
            from importlib import reload
            import src.config as cfg_mod
            reload(cfg_mod)
            issues = cfg_mod.get_settings().validate_llm_config()
            assert any("LLM_PROVIDER" in i for i in issues)

    def test_using_llamacpp_property(self):
        with patch.dict(os.environ, {"LLM_PROVIDER": "llamacpp", "ANTHROPIC_API_KEY": ""}):
            from importlib import reload
            import src.config as cfg_mod
            reload(cfg_mod)
            s = cfg_mod.get_settings()
            assert s.using_llamacpp is True
            assert s.using_anthropic is False

    def test_using_anthropic_property(self):
        with patch.dict(os.environ, {"LLM_PROVIDER": "anthropic", "ANTHROPIC_API_KEY": "key"}):
            from importlib import reload
            import src.config as cfg_mod
            reload(cfg_mod)
            s = cfg_mod.get_settings()
            assert s.using_anthropic is True
            assert s.using_llamacpp is False


# ─────────────────────────────────────────────────────────────────────────────
# Agent provider-agnostic tests
# (verify agents accept any BaseChatModel, not just ChatAnthropic)
# ─────────────────────────────────────────────────────────────────────────────

class TestAgentsProviderAgnostic:
    """
    These tests inject a generic MagicMock as the LLM.
    They prove that no agent is coupled to a specific provider class.
    """

    def _mock_llm(self, response_text: str) -> MagicMock:
        llm = MagicMock()
        resp = MagicMock()
        resp.content = response_text
        resp.usage_metadata = None
        llm.invoke.return_value = resp
        return llm

    def test_orchestrator_accepts_any_llm(self):
        import json
        from src.agents.orchestrator import OrchestratorAgent
        from src.agent_state import AgentState

        llm = self._mock_llm(json.dumps({
            "reasoning": "test", "subtasks": [],
            "next_agent": "triage", "goal_satisfied": False,
        }))
        # Pass a raw MagicMock — not ChatAnthropic, not ChatOpenAI
        agent = OrchestratorAgent(llm=llm)
        state = AgentState(patient_id="P1", current_input="test")
        result = agent.plan(state)
        assert result is not None

    def test_triage_accepts_any_llm(self):
        import json
        from src.agents.triage_agent import TriageAgent
        from src.agent_state import AgentState

        llm = self._mock_llm(json.dumps({
            "severity_score": 3, "urgency_level": "routine",
            "primary_concern": "headache", "abcde_assessment": {},
            "reasoning": "mild symptoms",
        }))
        agent = TriageAgent(llm=llm)
        state = AgentState(patient_id="P1", current_input="mild headache")
        result = agent.assess(state)
        assert result.triage.severity_score >= 1

    def test_research_accepts_any_llm(self):
        import json
        from src.agents.research_agent import ResearchAgent
        from src.agent_state import AgentState, TriageResult, UrgencyLevel

        llm = self._mock_llm(json.dumps({
            "summary": "Rest and hydrate.", "guidelines_applied": ["PCG"],
            "confidence_score": 0.8, "key_actions": ["Rest"],
        }))
        agent = ResearchAgent(llm=llm, vector_store=None)
        state = AgentState(patient_id="P1", current_input="headache")
        state.triage = TriageResult(severity_score=3, urgency_level=UrgencyLevel.ROUTINE,
                                    primary_concern="headache")
        result = agent.retrieve(state)
        assert result.research.summary != ""

    def test_critic_accepts_any_llm(self):
        import json
        from src.agents.scheduler_critic_agents import CriticAgent
        from src.agent_state import AgentState, TriageResult, UrgencyLevel, ResearchResult

        llm = self._mock_llm(json.dumps({
            "quality_score": 0.85, "approved": True,
            "issues_found": [], "feedback": "Good.", "requires_human_review": False,
        }))
        agent = CriticAgent(llm=llm)
        state = AgentState(patient_id="P1", current_input="headache")
        state.triage = TriageResult(severity_score=3, urgency_level=UrgencyLevel.ROUTINE,
                                    primary_concern="headache")
        state.research = ResearchResult(summary="Rest.", confidence_score=0.8)
        result = agent.review(state)
        assert result.critic.approved is True

    def test_synthesizer_accepts_any_llm(self):
        from src.agents.synthesizer import Synthesizer
        from src.agent_state import AgentState, TriageResult, UrgencyLevel, ResearchResult, CriticResult

        llm = self._mock_llm("Rest and stay hydrated. If symptoms worsen, seek emergency care.")
        agent = Synthesizer(llm=llm)
        state = AgentState(patient_id="P1", current_input="headache")
        state.triage = TriageResult(severity_score=3, urgency_level=UrgencyLevel.ROUTINE,
                                    primary_concern="headache")
        state.research = ResearchResult(summary="Rest.", confidence_score=0.8)
        state.critic = CriticResult(quality_score=0.85, approved=True)
        result = agent.synthesize(state)
        assert result.final_response != ""


# ─────────────────────────────────────────────────────────────────────────────
# Download model script tests
# ─────────────────────────────────────────────────────────────────────────────

class TestDownloadModelScript:

    def test_model_catalogue_has_required_keys(self):
        from scripts.download_model import MODELS
        for mid, m in MODELS.items():
            assert "name"     in m, f"{mid} missing 'name'"
            assert "filename" in m, f"{mid} missing 'filename'"
            assert "url"      in m, f"{mid} missing 'url'"
            assert "ram_gb"   in m, f"{mid} missing 'ram_gb'"
            assert "size_gb"  in m, f"{mid} missing 'size_gb'"
            assert "quality"  in m, f"{mid} missing 'quality'"

    def test_check_llamacpp_server_unreachable(self):
        from scripts.download_model import check_llamacpp_server
        # Port 19999 is almost certainly not in use
        result = check_llamacpp_server("http://localhost:19999")
        assert result is False

    def test_download_unknown_model_exits(self):
        from scripts.download_model import download_model
        with pytest.raises(SystemExit):
            download_model("nonexistent-model-xyz", dest_dir="/tmp")

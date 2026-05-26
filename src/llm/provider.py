"""
LLM Provider Factory
====================
Single place that decides WHICH language model to use.

Switch providers by changing one env var — no code changes needed:

    LLM_PROVIDER=anthropic   → Claude (cloud, best quality)
    LLM_PROVIDER=llamacpp    → llama.cpp server (local, zero API cost)

Both return a LangChain BaseChatModel, so every agent works identically
regardless of which provider is active.

──────────────────────────────────────────────────────────────────────────
HOW llama.cpp SERVER WORKS
──────────────────────────────────────────────────────────────────────────
llama.cpp exposes an OpenAI-compatible REST API when launched with:

    ./llama-server -m models/llama-3.1-8b-instruct.gguf \\
        --host 0.0.0.0 --port 8080 \\
        --n-gpu-layers 0            # 0 = CPU only
        --threads 4

We use LangChain's ChatOpenAI pointed at localhost:8080 — it speaks the
same /v1/chat/completions protocol that llama.cpp serves.

──────────────────────────────────────────────────────────────────────────
CHOOSING A MODEL
──────────────────────────────────────────────────────────────────────────
For healthcare triage we recommend:

| Model file                            | RAM  | Quality   | Speed   |
|---------------------------------------|------|-----------|---------|
| llama-3.1-8b-instruct.Q4_K_M.gguf    | 6 GB | Good ✓    | Fast    |
| llama-3.1-8b-instruct.Q8_0.gguf      | 8 GB | Better ✓✓ | Medium  |
| mistral-7b-instruct-v0.3.Q4_K_M.gguf | 5 GB | Good ✓    | Fast    |
| phi-3-mini-4k-instruct.Q4_K_M.gguf   | 3 GB | Basic     | V.Fast  |

Download from: https://huggingface.co/bartowski or TheBloke on HuggingFace
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel

from src.config import settings
from src.observability.logging import get_logger

log = get_logger(__name__)


# ── Public factory ────────────────────────────────────────────────────────────

def get_llm(
    *,
    temperature: float | None = None,
    max_tokens: int | None = None,
    streaming: bool = True,
) -> BaseChatModel:
    """
    Return the active LLM as a LangChain BaseChatModel.

    Uses settings.llm_provider to decide which backend to use.
    Falls back safely if the selected provider fails to initialise.

    Args:
        temperature:  Override default temperature (settings.llm_temperature)
        max_tokens:   Override default max tokens (settings.llm_max_tokens)
        streaming:    Enable streaming mode (token-by-token output)

    Returns:
        BaseChatModel (ChatAnthropic or ChatOpenAI wrapping llama.cpp)

    Raises:
        RuntimeError: if provider config is invalid and no fallback is available
    """
    temp   = temperature if temperature is not None else settings.llm_temperature
    tokens = max_tokens  if max_tokens  is not None else settings.llm_max_tokens

    # Validate config before attempting to build
    issues = settings.validate_llm_config()
    if issues:
        raise RuntimeError("LLM config errors:\n" + "\n".join(f"  - {i}" for i in issues))

    if settings.using_anthropic:
        return _build_anthropic(temperature=temp, max_tokens=tokens, streaming=streaming)
    elif settings.using_llamacpp:
        return _build_llamacpp(temperature=temp, max_tokens=tokens, streaming=streaming)
    else:
        raise RuntimeError(f"Unknown LLM_PROVIDER: '{settings.llm_provider}'")


def get_provider_info() -> dict[str, Any]:
    """
    Return a dict describing the active provider — useful for /health endpoint
    and startup logs. Never includes API keys.
    """
    if settings.using_anthropic:
        return {
            "provider":     "anthropic",
            "model":        settings.llm_model,
            "api_key_set":  bool(settings.anthropic_api_key),
        }
    elif settings.using_llamacpp:
        return {
            "provider":     "llamacpp",
            "model":        settings.llamacpp_model,
            "base_url":     settings.llamacpp_base_url,
            "n_ctx":        settings.llamacpp_n_ctx,
            "n_threads":    settings.llamacpp_n_threads,
            "n_gpu_layers": settings.llamacpp_n_gpu_layers,
        }
    return {"provider": "unknown"}


def check_provider_health() -> dict[str, Any]:
    """
    Lightweight connectivity check for the active LLM provider.
    Returns {"ok": bool, "latency_ms": int, "error": str|None}
    """
    import time
    start = time.perf_counter()
    try:
        llm = get_llm(max_tokens=5, temperature=0.0)
        from langchain_core.messages import HumanMessage
        llm.invoke([HumanMessage(content="ping")])
        return {
            "ok": True,
            "latency_ms": round((time.perf_counter() - start) * 1000),
            "error": None,
            **get_provider_info(),
        }
    except Exception as exc:
        return {
            "ok": False,
            "latency_ms": round((time.perf_counter() - start) * 1000),
            "error": str(exc)[:200],
            **get_provider_info(),
        }


# ── Private builders ──────────────────────────────────────────────────────────

def _build_anthropic(
    temperature: float,
    max_tokens: int,
    streaming: bool,
) -> BaseChatModel:
    """Build and return a ChatAnthropic instance."""
    try:
        from langchain_anthropic import ChatAnthropic
    except ImportError as e:
        raise RuntimeError(
            "langchain-anthropic is not installed. "
            "Run: pip install langchain-anthropic"
        ) from e

    log.info(
        "llm_provider_init",
        provider="anthropic",
        model=settings.llm_model,
        temperature=temperature,
        max_tokens=max_tokens,
    )

    return ChatAnthropic(
        model=settings.llm_model,
        max_tokens=max_tokens,
        temperature=temperature,
        streaming=streaming,
        anthropic_api_key=settings.anthropic_api_key,
    )


def _build_llamacpp(
    temperature: float,
    max_tokens: int,
    streaming: bool,
) -> BaseChatModel:
    """
    Build a ChatOpenAI instance pointed at the local llama.cpp server.

    llama.cpp's server exposes an OpenAI-compatible API at:
        POST {base_url}/v1/chat/completions

    We use langchain_openai.ChatOpenAI as the client — no OpenAI account
    needed; openai_api_key is set to "not-needed" to satisfy the library.
    """
    try:
        from langchain_openai import ChatOpenAI
    except ImportError as e:
        raise RuntimeError(
            "langchain-openai is not installed. "
            "Run: pip install langchain-openai"
        ) from e

    base_url = settings.llamacpp_base_url.rstrip("/") + "/v1"

    log.info(
        "llm_provider_init",
        provider="llamacpp",
        model=settings.llamacpp_model,
        base_url=base_url,
        temperature=temperature,
        max_tokens=max_tokens,
        n_threads=settings.llamacpp_n_threads,
        n_gpu_layers=settings.llamacpp_n_gpu_layers,
    )

    return ChatOpenAI(
    model=settings.llamacpp_model,
    base_url=base_url,
    api_key="not-needed",
    max_tokens=max_tokens,
    temperature=temperature,
    streaming=streaming,
)

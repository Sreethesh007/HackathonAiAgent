"""
FastAPI REST API — exposes the healthcare triage pipeline over HTTP.

Endpoints:
  POST /triage                          — start a new triage session
  POST /triage/{session_id}/continue    — continue a session (or submit HITL decision)
  GET  /triage/{session_id}/status      — inspect session state
  GET  /health                          — liveness + readiness
  GET  /metrics                         — Prometheus metrics (text format)

Auth:       Bearer JWT (HS256)
Rate limit: 10 req/min per patient_id (configurable)
"""

from __future__ import annotations

import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from src.api.auth import get_current_user, TokenData
from src.api.login import router as auth_router
from src.api.schemas import (
    ContinueRequest,
    ContinueResponse,
    HealthResponse,
    ProviderInfoResponse,
    TriageRequest,
    TriageResponse,
    SessionStatusResponse,
    ErrorDetail,
)
from src.config import settings
from src.graph.pipeline import HealthcareTriageGraph
from src.agents.research_agent import ResearchAgent
from src.memory import KnowledgeRetriever
from src.llm.provider import check_provider_health, get_provider_info
from src.observability.logging import configure_logging, get_logger
from src.observability.metrics import ACTIVE_SESSIONS, API_LATENCY, API_REQUESTS

log = get_logger(__name__)

# ── Application startup ──────────────────────────────────────────────────────

_pipeline: HealthcareTriageGraph | None = None
_retriever: KnowledgeRetriever | None = None
_start_time = time.time()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle."""
    global _pipeline, _retriever

    configure_logging()
    settings.ensure_dirs()

    # Validate LLM config before starting — fail fast with a clear message
    issues = settings.validate_llm_config()
    if issues:
        for issue in issues:
            log.error("llm_config_error", detail=issue)
        raise RuntimeError("Invalid LLM configuration. Check your .env file.\n" + "\n".join(issues))

    provider_info = get_provider_info()
    log.info(
        "api_startup",
        environment=settings.environment,
        llm_provider=provider_info["provider"],
        llm_model=provider_info.get("model", "unknown"),
    )

    # Initialise the knowledge retriever (ChromaDB + sentence-transformers)
    try:
        _retriever = KnowledgeRetriever()
        kb_health = _retriever.health_check()
        log.info("knowledge_base_ready", **kb_health)
        if kb_health.get("document_count", 0) == 0:
            log.warning(
                "knowledge_base_empty",
                hint="Run: python scripts/seed_knowledge.py --reset",
            )
    except Exception as exc:
        log.error(
            "knowledge_retriever_init_failed",
            error=str(exc),
            hint="API will start but RAG will use fallback guidelines.",
        )
        _retriever = None

    # Build pipeline — inject retriever into ResearchAgent
    research_agent = ResearchAgent(vector_store=_retriever)
    _pipeline = HealthcareTriageGraph(research=research_agent)
    _pipeline.export_mermaid()   # write graph diagram to docs/
    log.info("pipeline_ready")

    ACTIVE_SESSIONS.set(0)
    yield

    log.info("api_shutdown")


# ── FastAPI app ──────────────────────────────────────────────────────────────

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="Healthcare Triage Agent API",
    description="Autonomous multi-agent triage system — powered by LangGraph + Claude",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Auth router (login endpoint for Angular frontend) ─────────────────────────
app.include_router(auth_router)


# ── Request ID + latency middleware ──────────────────────────────────────────

@app.middleware("http")
async def request_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    start = time.perf_counter()

    import structlog
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(request_id=request_id)

    response = await call_next(request)

    latency = time.perf_counter() - start
    endpoint = request.url.path
    API_REQUESTS.labels(
        method=request.method,
        endpoint=endpoint,
        status_code=str(response.status_code),
    ).inc()
    API_LATENCY.labels(endpoint=endpoint).observe(latency)

    response.headers["X-Request-ID"] = request_id
    response.headers["X-Response-Time"] = f"{latency*1000:.1f}ms"
    return response


# ── Global exception handler (RFC 7807 Problem+JSON) ────────────────────────

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    log.error("unhandled_exception", error=str(exc), path=request.url.path)
    return JSONResponse(
        status_code=500,
        content={
            "type": "https://example.com/errors/internal",
            "title": "Internal Server Error",
            "status": 500,
            "detail": "An unexpected error occurred. Please try again.",
            "instance": request.url.path,
        },
        media_type="application/problem+json",
    )


# ── Health ───────────────────────────────────────────────────────────────────

@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health():
    """Liveness + readiness probe — includes active LLM provider info."""
    provider = get_provider_info()
    return HealthResponse(
        status="ok",
        version="1.0.0",
        uptime_seconds=round(time.time() - _start_time),
        environment=settings.environment,
        pipeline_ready=_pipeline is not None,
        llm_provider=provider["provider"],
        llm_model=provider.get("model", "unknown"),
    )


@app.get("/health/llm", response_model=ProviderInfoResponse, tags=["System"])
async def health_llm(current_user: TokenData = Depends(get_current_user)):
    """
    Deep LLM provider health check — sends a real ping to the active provider.
    Use this to verify the LLM is reachable before running triage.
    """
    result = check_provider_health()
    status_code = 200 if result["ok"] else 503
    return JSONResponse(content=result, status_code=status_code)


# ── Metrics ──────────────────────────────────────────────────────────────────

@app.get("/health/knowledge", tags=["System"])
async def health_knowledge():
    """
    Knowledge base health check — returns document count, embedding model,
    and a sample retrieval to verify the vector store is seeded and responsive.

    If document_count is 0, run: python scripts/seed_knowledge.py --reset
    """
    if _retriever is None:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unavailable",
                "error": "KnowledgeRetriever failed to initialise. Check startup logs.",
                "hint": "Run: python scripts/seed_knowledge.py --reset",
            },
        )
    result = _retriever.health_check()
    status_code = 200 if result.get("status") == "ok" else 503
    return JSONResponse(content=result, status_code=status_code)


@app.get("/metrics", tags=["System"])
async def metrics():
    """Prometheus metrics endpoint."""
    return PlainTextResponse(
        content=generate_latest().decode("utf-8"),
        media_type=CONTENT_TYPE_LATEST,
    )


# ── Triage — start new session ───────────────────────────────────────────────

@app.post("/triage", response_model=TriageResponse, status_code=200, tags=["Triage"])
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
async def start_triage(
    request: Request,
    body: TriageRequest,
    current_user: TokenData = Depends(get_current_user),
):
    """
    Start a new triage session for a patient message.

    Returns a triage assessment, clinical recommendations, and (if applicable)
    an appointment confirmation.
    """
    if _pipeline is None:
        raise HTTPException(status_code=503, detail="Pipeline not ready")

    log.info(
        "triage_request",
        patient_id=body.patient_id,   # redacted in production
        session_id=body.session_id,
    )

    ACTIVE_SESSIONS.inc()
    try:
        state = _pipeline.run(
            patient_id=body.patient_id,
            message=body.message,
            session_id=body.session_id,
        )
    except Exception as exc:
        log.error("triage_pipeline_error", error=str(exc))
        raise HTTPException(status_code=500, detail="Triage pipeline failed")
    finally:
        ACTIVE_SESSIONS.dec()

    return _state_to_triage_response(state)


# ── Triage — continue / HITL approval ────────────────────────────────────────

@app.post("/triage/{session_id}/continue", response_model=ContinueResponse, tags=["Triage"])
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
async def continue_triage(
    request: Request,
    session_id: str,
    body: ContinueRequest,
    current_user: TokenData = Depends(get_current_user),
):
    """
    Continue a triage session.

    - If the session is awaiting human review: pass `human_approval=true/false`
    - Otherwise: send a follow-up `message` to continue the conversation
    """
    if _pipeline is None:
        raise HTTPException(status_code=503, detail="Pipeline not ready")

    ACTIVE_SESSIONS.inc()
    try:
        if body.human_approval is not None:
            # HITL path: resume paused session with human decision
            state = _pipeline.resume(session_id=session_id, human_approved=body.human_approval)
        elif body.message:
            # New turn in same session
            state = _pipeline.run(
                patient_id=body.patient_id or "unknown",
                message=body.message,
                session_id=session_id,
            )
        else:
            raise HTTPException(status_code=422, detail="Provide either 'message' or 'human_approval'")
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        log.error("continue_pipeline_error", error=str(exc))
        raise HTTPException(status_code=500, detail="Pipeline continuation failed")
    finally:
        ACTIVE_SESSIONS.dec()

    return ContinueResponse(
        session_id=state.session_id,
        response=state.final_response,
        flow_status=str(state.flow_status),
        requires_human_review=state.requires_human_review,
        severity_score=state.triage.severity_score,
        urgency_level=str(state.triage.urgency_level),
    )


# ── Session status ────────────────────────────────────────────────────────────

@app.get("/triage/{session_id}/status", response_model=SessionStatusResponse, tags=["Triage"])
async def session_status(
    session_id: str,
    current_user: TokenData = Depends(get_current_user),
):
    """Inspect the current state of a triage session (useful for polling)."""
    if _pipeline is None:
        raise HTTPException(status_code=503, detail="Pipeline not ready")

    config = {"configurable": {"thread_id": session_id}}
    checkpoint = _pipeline._graph.get_state(config)
    if checkpoint is None or not checkpoint.values:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

    from src.agent_state import AgentState
    state = AgentState.model_validate(checkpoint.values)

    return SessionStatusResponse(
        session_id=session_id,
        flow_status=str(state.flow_status),
        iteration_count=state.iteration_count,
        max_iterations=state.max_iterations,
        requires_human_review=state.requires_human_review,
        severity_score=state.triage.severity_score,
        urgency_level=str(state.triage.urgency_level),
        appointment_booked=state.appointment.booked,
        appointment_id=state.appointment.appointment_id or None,
        created_at=state.created_at.isoformat(),
        updated_at=state.updated_at.isoformat(),
    )


# ── Internal helper ───────────────────────────────────────────────────────────

def _state_to_triage_response(state) -> TriageResponse:
    from src.agent_state import AgentState
    return TriageResponse(
        session_id=state.session_id,
        response=state.final_response,
        severity_score=state.triage.severity_score,
        urgency_level=str(state.triage.urgency_level),
        primary_concern=state.triage.primary_concern,
        sources=[s.get("title", "") for s in state.research.sources],
        guidelines_applied=state.research.guidelines_applied,
        appointment_booked=state.appointment.booked,
        appointment_id=state.appointment.appointment_id or None,
        appointment_datetime=state.appointment.datetime_iso or None,
        appointment_provider=state.appointment.provider or None,
        requires_human_review=state.requires_human_review,
        quality_score=state.critic.quality_score,
        iteration_count=state.iteration_count,
        reasoning_trace=state.reasoning_trace,
    )

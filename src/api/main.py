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
from fastapi.responses import JSONResponse, PlainTextResponse, StreamingResponse
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from src.api.auth import get_current_user, TokenData
from src.api.login import router as auth_router
from src.api import conversation_store
from src.api.schemas import (
    ContinueRequest,
    ContinueResponse,
    ConversationMessage,
    HealthResponse,
    ProviderInfoResponse,
    SaveMessageRequest,
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
from src.db import init_db, add_appointment, get_all_appointments as db_get_appointments

log = get_logger(__name__)

# ── Application startup ──────────────────────────────────────────────────────

_pipeline: HealthcareTriageGraph | None = None
_retriever: KnowledgeRetriever | None = None
_start_time = time.time()
_patient_sessions = __import__('collections').defaultdict(list)
# Stores sessions awaiting clinician review: session_id -> SessionStatusResponse-like dict
_pending_review_sessions: dict = {}
# Stores booked appointments
_appointments = []

# SSE Event Generator Helper
def _extract_text_from_chunk(chunk_content) -> str:
    """Extract plain text from LLM chunk content.
    
    Anthropic/Claude returns a list of content blocks like:
        [{"type": "text", "text": "hello"}, ...]
    OpenAI/others return a plain string.
    This helper normalises both forms.
    """
    if isinstance(chunk_content, str):
        return chunk_content
    if isinstance(chunk_content, list):
        parts = []
        for block in chunk_content:
            if isinstance(block, dict):
                parts.append(block.get("text", ""))
            elif isinstance(block, str):
                parts.append(block)
            else:
                # AIMessageChunk sub-objects (e.g. TextBlock)
                text = getattr(block, "text", None)
                if text:
                    parts.append(text)
        return "".join(parts)
    return ""


def _extract_node_reasoning(node: str, state_dict: dict) -> str:
    """Extract a human-readable reasoning string from an agent node's output state.

    Non-streaming agents (triage, research, critic, scheduler) use llm.invoke(),
    so their reasoning never appears in on_chat_model_stream. We pull it from the
    state dict that is emitted in on_chain_end instead.
    """
    if node == "triage":
        t = state_dict.get("triage", {})
        if isinstance(t, dict):
            parts = []
            if t.get("reasoning"):
                parts.append(t["reasoning"])
            score = t.get("severity_score")
            urgency = t.get("urgency_level")
            concern = t.get("primary_concern")
            if score and urgency:
                parts.append(f"Severity: {score}/10 · Urgency: {urgency}")
            if concern:
                parts.append(f"Primary concern: {concern}")
            return " — ".join(parts) if parts else ""

    if node == "research":
        r = state_dict.get("research", {})
        if isinstance(r, dict):
            summary = r.get("summary", "")
            guidelines = r.get("guidelines_applied", [])
            confidence = r.get("confidence_score", 0)
            parts = []
            if summary:
                parts.append(summary[:400])
            if guidelines:
                parts.append(f"Guidelines applied: {', '.join(guidelines[:3])}")
            if confidence:
                parts.append(f"Confidence: {confidence:.0%}")
            return " — ".join(parts) if parts else ""

    if node == "critic":
        c = state_dict.get("critic", {})
        if isinstance(c, dict):
            score = c.get("quality_score", 0)
            approved = c.get("approved", False)
            feedback = c.get("feedback", "")
            issues = c.get("issues_found", [])
            verdict = "✅ Approved" if approved else "⚠️ Needs review"
            parts = [f"{verdict} (quality score: {score:.0%})"]
            if feedback:
                parts.append(feedback[:300])
            if issues:
                parts.append(f"Issues: {'; '.join(issues[:2])}")
            return " — ".join(parts) if parts else ""

    if node == "scheduler":
        s = state_dict.get("appointment", {})
        if isinstance(s, dict):
            booked = s.get("booked", False)
            if booked:
                return f"✅ Appointment booked with {s.get('provider')} on {s.get('datetime_iso')} at {s.get('location')}"
            else:
                return "❌ No suitable appointment found or booking failed."



    return ""


async def event_generator(pipeline_iterator, patient_id: str, session_id: str):
    import json
    final_state = None
    try:
        async for event in pipeline_iterator:
            kind = event["event"]

            # ── Notify frontend when a new agent node starts ───────────────
            if kind == "on_chain_start":
                node = event.get("metadata", {}).get("langgraph_node")
                # Only emit for known specialist nodes (not internal chain wrappers)
                KNOWN_NODES = {
                    "orchestrator", "triage", "research",
                    "scheduler", "critic", "human_review", "synthesizer"
                }
                if node and node in KNOWN_NODES:
                    yield f"data: {json.dumps({'type': 'step_start', 'node': node})}\n\n"

            # ── Stream LLM tokens ──────────────────────────────────────────
            elif kind == "on_chat_model_stream":
                node = event.get("metadata", {}).get("langgraph_node", "unknown")
                raw_content = event["data"]["chunk"].content
                chunk_text = _extract_text_from_chunk(raw_content)
                if chunk_text:
                    if node == "synthesizer":
                        yield f"data: {json.dumps({'type': 'message', 'content': chunk_text})}\n\n"
                    else:
                        yield f"data: {json.dumps({'type': 'thinking', 'content': chunk_text, 'node': node})}\n\n"

            # ── Capture final state + emit per-node reasoning ─────────────
            elif kind in ("on_chain_end", "on_graph_end"):
                node = event.get("metadata", {}).get("langgraph_node")
                out = event["data"].get("output")

                if isinstance(out, dict):
                    # Capture the final graph state when flow_status is present
                    if "flow_status" in out:
                        final_state = out
                        log.debug("pipeline_state_captured", event_name=event.get("name"))

                    # Extract and emit per-agent reasoning for non-streaming agents.
                    # These agents use llm.invoke() so no on_chat_model_stream fires.
                    if node and node in {"triage", "research", "critic", "scheduler"}:
                        reasoning = _extract_node_reasoning(node, out)
                        if reasoning:
                            yield f"data: {json.dumps({'type': 'step_content', 'node': node, 'content': reasoning})}\n\n"

    except Exception as exc:
        log.error("streaming_error", error=str(exc))
        yield f"data: {json.dumps({'type': 'error', 'content': str(exc)})}\n\n"

    # Always emit a metadata event so the frontend can clear "AI is thinking"
    # and update session flags, even if we never captured a full state dict.
    
    def _to_dict(obj):
        if not obj: return {}
        if isinstance(obj, dict): return obj
        if hasattr(obj, "model_dump"): return obj.model_dump()
        return vars(obj)

    triage_state = _to_dict(final_state.get("triage")) if final_state else {}
    appt_data = _to_dict(final_state.get("appointment")) if final_state else {}

    meta = {
        "type": "metadata",
        "offer_appointment": False,
        "appointment_booked": False,
        "requires_human_review": False,
        "session_id": session_id,
        "flow_status": "completed",
        "triage_severity": None,
        "triage_urgency": None,
        "triage_concern": None,
    }
    if final_state:
        meta.update({
            "offer_appointment": final_state.get("offer_appointment", False),
            "appointment_booked": appt_data.get("booked", False),
            "requires_human_review": final_state.get("requires_human_review", False),
            "flow_status": final_state.get("flow_status", "completed"),
            "triage_severity": triage_state.get("severity_score") or triage_state.get("severity"),
            "triage_urgency": triage_state.get("urgency_level") or triage_state.get("urgency"),
            "triage_concern": triage_state.get("primary_concern") or triage_state.get("concern"),
            "final_response": final_state.get("final_response", ""),
        })

        # Update in-memory session history
        session_entry = {
            "session_id": session_id,
            "created_at": final_state.get("created_at"),
            "updated_at": final_state.get("updated_at"),
            "status": final_state.get("flow_status"),
            "summary": final_state.get("current_input", "")[:50]
        }
        existing = next((s for s in _patient_sessions[patient_id] if s["session_id"] == session_id), None)
        if existing:
            existing.update(session_entry)
        else:
            _patient_sessions[patient_id].append(session_entry)

        # Track appointments
        if appt_data.get("booked"):
            appt_id = appt_data.get("appointment_id")
            if appt_id:
                add_appointment({
                    "appointment_id": appt_id,
                    "datetime_iso": appt_data.get("datetime_iso"),
                    "provider": appt_data.get("provider"),
                    "location": appt_data.get("location"),
                    "patient_name": appt_data.get("patient_name", "Unknown"),
                    "patient_age": appt_data.get("patient_age", "Unknown"),
                    "reason": triage_state.get("primary_concern", "N/A"),
                    "session_id": session_id
                })

        # Track sessions that need clinician review
        if final_state.get("requires_human_review", False):
            _pending_review_sessions[session_id] = {
                "session_id": session_id,
                "flow_status": final_state.get("flow_status", "awaiting_human"),
                "iteration_count": final_state.get("iteration_count", 0),
                "max_iterations": final_state.get("max_iterations", 10),
                "requires_human_review": True,
                "severity_score": final_state.get("triage", {}).get("severity_score", 0),
                "urgency_level": final_state.get("triage", {}).get("urgency_level", "unknown"),
                "appointment_booked": final_state.get("appointment", {}).get("booked", False),
                "appointment_id": final_state.get("appointment", {}).get("appointment_id") or None,
                "created_at": final_state.get("created_at", ""),
                "updated_at": final_state.get("updated_at", ""),
                "summary": final_state.get("current_input", "")[:80],
            }
        else:
            # Remove from pending if it was previously there (e.g. after re-run)
            _pending_review_sessions.pop(session_id, None)

    yield f"data: {json.dumps(meta)}\n\n"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle."""
    global _pipeline, _retriever

    configure_logging()
    settings.ensure_dirs()
    init_db()

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

    # Initialise SQLite conversation store
    conversation_store.init_db()
    log.info("conversation_store_ready", db_path="data/conversations.db")

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

@app.post("/triage", tags=["Triage"])
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
async def start_triage(
    request: Request,
    body: TriageRequest,
    current_user: TokenData = Depends(get_current_user),
):
    """
    Start a new triage session for a patient message, streaming back tokens.
    """
    if _pipeline is None:
        raise HTTPException(status_code=503, detail="Pipeline not ready")

    patient_id = body.patient_id or current_user.sub
    session_id = body.session_id or str(uuid.uuid4())

    log.info(
        "triage_request_stream",
        patient_id=patient_id,
        session_id=session_id,
    )

    ACTIVE_SESSIONS.inc()
    
    # We dec() inside a background task or just not do it for streaming easily. 
    # For simplicity, we just use the generator.
    async def stream():
        try:
            async for chunk in event_generator(
                _pipeline.astream_run(patient_id=patient_id, message=body.message, session_id=session_id),
                patient_id=patient_id,
                session_id=session_id
            ):
                yield chunk
        finally:
            ACTIVE_SESSIONS.dec()

    return StreamingResponse(stream(), media_type="text/event-stream")


# ── Triage — continue / HITL approval ────────────────────────────────────────

@app.post("/triage/{session_id}/continue", tags=["Triage"])
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
async def continue_triage(
    request: Request,
    session_id: str,
    body: ContinueRequest,
    current_user: TokenData = Depends(get_current_user),
):
    """Continue a triage session via SSE stream."""
    if _pipeline is None:
        raise HTTPException(status_code=503, detail="Pipeline not ready")

    patient_id = body.patient_id or current_user.sub
    ACTIVE_SESSIONS.inc()
    
    async def stream():
        try:
            if body.human_approval is not None:
                # Clinician has made a decision — remove from the pending queue immediately
                _pending_review_sessions.pop(session_id, None)
                pipeline_iterator = _pipeline.astream_resume(session_id=session_id, human_approved=body.human_approval)
            elif body.message:
                pipeline_iterator = _pipeline.astream_run(patient_id=patient_id, message=body.message, session_id=session_id)
            else:
                yield f"data: {{\"type\": \"error\", \"content\": \"Provide either message or human_approval\"}}\n\n"
                return

            async for chunk in event_generator(pipeline_iterator, patient_id=patient_id, session_id=session_id):
                yield chunk
        except Exception as exc:
            log.error("continue_pipeline_error", error=str(exc))
            yield f"data: {{\"type\": \"error\", \"content\": \"{str(exc)}\"}}\n\n"
        finally:
            ACTIVE_SESSIONS.dec()

    return StreamingResponse(stream(), media_type="text/event-stream")

@app.get("/sessions", tags=["Triage"])
async def get_sessions(current_user: TokenData = Depends(get_current_user)):
    """Fetch all sessions for the current patient."""
    patient_id = current_user.sub
    return {"sessions": _patient_sessions.get(patient_id, [])}


# ── Conversation history (SQLite-backed) ──────────────────────────────────────

@app.post("/api/conversations", tags=["Conversations"], status_code=201)
async def save_conversation_message(
    body: SaveMessageRequest,
    current_user: TokenData = Depends(get_current_user),
):
    """Persist a single conversation message turn.

    The frontend calls this immediately after the user sends a message so the
    user turn is stored even before the pipeline responds.  The assistant turn
    is also saveable via this endpoint if needed.
    """
    effective_user_id = body.user_id or current_user.sub
    if body.role not in ("user", "assistant"):
        raise HTTPException(status_code=422, detail="role must be 'user' or 'assistant'")

    row_id = conversation_store.save_message(
        session_id=body.session_id,
        user_id=effective_user_id,
        role=body.role,
        message=body.message,
    )
    log.info(
        "conversation_message_saved",
        session_id=body.session_id,
        role=body.role,
        row_id=row_id,
    )
    return {"id": row_id, "status": "saved"}


@app.get("/api/conversations/{session_id}", tags=["Conversations"])
async def get_conversation_history(
    session_id: str,
    current_user: TokenData = Depends(get_current_user),
):
    """Return the full message history for a session, ordered by timestamp.

    Returns an empty list (not 404) when the session has no stored messages,
    so the frontend can distinguish "new session" from "session not found".
    """
    messages = conversation_store.get_messages(session_id)
    return {"session_id": session_id, "messages": messages}


@app.get("/clinician/pending", tags=["Clinician"])
async def get_pending_reviews(current_user: TokenData = Depends(get_current_user)):
    """Return all sessions currently awaiting clinician (HITL) review.

    Accessible by clinicians only — in production add a role check here.
    For now we return all pending sessions regardless of who triggers it.
    """
    return {"sessions": list(_pending_review_sessions.values())}

@app.get("/clinician/appointments", tags=["Clinician"])
async def get_all_appointments_api(current_user: TokenData = Depends(get_current_user)):
    """Return all booked appointments for the clinician dashboard."""
    return {"appointments": db_get_appointments()}


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

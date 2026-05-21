"""
Structured logging using structlog.

- Development: colourised, human-readable console output
- Production:  JSON renderer, PII fields automatically redacted

Usage:
    from src.observability.logging import get_logger
    log = get_logger(__name__)
    log.info("agent_called", agent="triage", session_id="abc123")
"""

from __future__ import annotations

import hashlib
import logging
import sys

import structlog
from structlog.types import EventDict, WrappedLogger

from src.config import settings

# Fields whose VALUES must be hashed in production
_PII_FIELDS = {"patient_id", "current_input", "message_content", "patient_name"}


def _redact_pii(logger: WrappedLogger, method: str, event_dict: EventDict) -> EventDict:
    """structlog processor — replaces PII values with SHA-256 prefix."""
    if not settings.is_production:
        return event_dict
    for field in _PII_FIELDS:
        if field in event_dict and event_dict[field]:
            raw = str(event_dict[field])
            event_dict[field] = "sha:" + hashlib.sha256(raw.encode()).hexdigest()[:12]
    return event_dict


def _add_service_info(logger: WrappedLogger, method: str, event_dict: EventDict) -> EventDict:
    event_dict.setdefault("service", "healthcare-triage-agent")
    event_dict.setdefault("environment", settings.environment)
    return event_dict


def configure_logging() -> None:
    """Call once at application startup."""
    shared_processors: list = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        _add_service_info,
        _redact_pii,
        structlog.processors.StackInfoRenderer(),
    ]

    if settings.is_production:
        renderer = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    structlog.configure(
        processors=shared_processors + [
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
        foreign_pre_chain=shared_processors,
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(settings.log_level.upper())

    # Silence noisy third-party loggers
    for noisy in ("httpx", "httpcore", "chromadb", "urllib3"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name)

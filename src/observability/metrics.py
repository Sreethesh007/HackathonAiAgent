"""
Prometheus metrics — all counters/histograms/gauges defined here once
and imported wherever needed.

Metrics exposed at GET /metrics (see api/main.py).
"""

from prometheus_client import Counter, Gauge, Histogram

# ── Agent calls ────────────────────────────────────────────────────────────
AGENT_CALLS = Counter(
    "agent_calls_total",
    "Total agent invocations",
    ["agent", "status"],          # status: success | error | timeout
)

AGENT_LATENCY = Histogram(
    "agent_latency_seconds",
    "Agent call duration in seconds",
    ["agent"],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0],
)

# ── Tool calls ─────────────────────────────────────────────────────────────
TOOL_CALLS = Counter(
    "tool_calls_total",
    "Total tool invocations",
    ["tool", "status"],
)

# ── Pipeline-level ─────────────────────────────────────────────────────────
ACTIVE_SESSIONS = Gauge(
    "active_sessions",
    "Number of in-progress triage sessions",
)

HUMAN_REVIEWS = Counter(
    "human_reviews_requested_total",
    "Sessions routed to human review",
)

FLOW_COMPLETIONS = Counter(
    "flow_completions_total",
    "Completed triage flows",
    ["urgency_level"],            # emergency | urgent | routine | unknown
)

FLOW_FAILURES = Counter(
    "flow_failures_total",
    "Failed triage flows",
    ["reason"],
)

# ── API ────────────────────────────────────────────────────────────────────
API_REQUESTS = Counter(
    "api_requests_total",
    "Total API requests",
    ["method", "endpoint", "status_code"],
)

API_LATENCY = Histogram(
    "api_request_latency_seconds",
    "API request latency",
    ["endpoint"],
    buckets=[0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)

# ── LLM token usage ────────────────────────────────────────────────────────
LLM_TOKENS_USED = Counter(
    "llm_tokens_total",
    "Cumulative LLM token usage",
    ["agent", "token_type"],      # token_type: input | output
)

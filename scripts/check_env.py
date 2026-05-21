#!/usr/bin/env python3
"""
Environment sanity checker — run before starting the app.

Checks:
  1. All required env vars are set and non-empty
  2. Data directories are writable
  3. Anthropic API key is reachable (lightweight ping)
  4. ChromaDB is importable (local mode — no server needed)

Exit code 0 = all clear, 1 = one or more failures.
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

# Ensure project root is in path
sys.path.insert(0, str(Path(__file__).parent.parent))

GREEN = "\033[92m"
RED   = "\033[91m"
RESET = "\033[0m"
BOLD  = "\033[1m"

passed = 0
failed = 0


def ok(label: str, detail: str = "") -> None:
    global passed
    passed += 1
    suffix = f"  ({detail})" if detail else ""
    print(f"  {GREEN}✓{RESET} {label}{suffix}")


def fail(label: str, detail: str = "") -> None:
    global failed
    failed += 1
    suffix = f"  ✗ {detail}" if detail else ""
    print(f"  {RED}✗{RESET} {label}{suffix}")


def section(title: str) -> None:
    print(f"\n{BOLD}{title}{RESET}")


# ── 1. Required environment variables ────────────────────────────────────────
section("Environment Variables")

REQUIRED_VARS = {
    "ANTHROPIC_API_KEY": "LLM access",
    "JWT_SECRET":        "API authentication",
    "CHROMA_PERSIST_DIR":"Vector store location",
    "SESSION_DIR":       "Session storage",
    "LOG_LEVEL":         "Logging configuration",
}

dotenv_path = Path(".env")
if dotenv_path.exists():
    from dotenv import load_dotenv
    load_dotenv()
    ok(".env file found")
else:
    fail(".env file", "not found — copy from .env.example")

for var, purpose in REQUIRED_VARS.items():
    value = os.getenv(var, "")
    if value and value not in ("your_key_here", "change_me", "change_me_to_a_long_random_string_in_production"):
        ok(f"{var}", purpose)
    else:
        fail(f"{var}", f"missing or placeholder ({purpose})")

# ── 2. Data directories ───────────────────────────────────────────────────────
section("Data Directories")

DIRS = [
    os.getenv("CHROMA_PERSIST_DIR", "./data/chroma"),
    os.getenv("SESSION_DIR", "./data/sessions"),
    os.getenv("FAILED_FLOWS_DIR", "./data/failed_flows"),
]

for d in DIRS:
    p = Path(d)
    p.mkdir(parents=True, exist_ok=True)
    try:
        test_file = p / ".write_test"
        test_file.write_text("ok")
        test_file.unlink()
        ok(str(p), "writable")
    except OSError as e:
        fail(str(p), f"not writable: {e}")

# ── 3. Python imports ─────────────────────────────────────────────────────────
section("Python Imports")

PACKAGES = {
    "langchain":      "LangChain core",
    "langgraph":      "Agent orchestration",
    "langchain_anthropic": "Anthropic LLM",
    "chromadb":       "Vector store",
    "fastapi":        "REST API",
    "pydantic":       "Data validation",
    "structlog":      "Structured logging",
    "prometheus_client": "Metrics",
    "tenacity":       "Retry logic",
    "jose":           "JWT auth",
}

for pkg, purpose in PACKAGES.items():
    try:
        __import__(pkg)
        ok(pkg, purpose)
    except ImportError as e:
        fail(pkg, f"not installed: {e}")

# ── 4. Anthropic API reachability ────────────────────────────────────────────
section("Anthropic API")

api_key = os.getenv("ANTHROPIC_API_KEY", "")
if api_key and api_key != "your_key_here":
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        start = time.perf_counter()
        msg = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=5,
            messages=[{"role": "user", "content": "ping"}],
        )
        latency_ms = round((time.perf_counter() - start) * 1000)
        ok("Anthropic API", f"reachable ({latency_ms}ms)")
    except Exception as e:
        fail("Anthropic API", str(e)[:80])
else:
    fail("Anthropic API", "ANTHROPIC_API_KEY not set — skip if running without LLM")

# ── 5. ChromaDB (local mode) ──────────────────────────────────────────────────
section("ChromaDB")

try:
    import chromadb
    persist_dir = os.getenv("CHROMA_PERSIST_DIR", "./data/chroma")
    client = chromadb.PersistentClient(path=persist_dir)
    collections = client.list_collections()
    ok("ChromaDB local client", f"persist_dir={persist_dir}, collections={len(collections)}")
except Exception as e:
    fail("ChromaDB", str(e)[:80])

# ── Summary ───────────────────────────────────────────────────────────────────
print(f"\n{'─'*45}")
total = passed + failed
print(f"  {GREEN}{passed}{RESET}/{total} checks passed  |  {RED}{failed}{RESET} failed")

if failed > 0:
    print(f"\n  {RED}Fix the failing checks before starting the application.{RESET}")
    sys.exit(1)
else:
    print(f"\n  {GREEN}All checks passed — ready to run!{RESET}")
    print("  Run: make run-dev")
    sys.exit(0)

#!/usr/bin/env python3
"""
Environment sanity checker — run before starting the app.
Handles both LLM_PROVIDER=anthropic and LLM_PROVIDER=llamacpp.

Exit code 0 = all clear, 1 = one or more failures.
"""
from __future__ import annotations
import os, sys, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

GREEN = "\033[92m"; RED = "\033[91m"; YELLOW = "\033[93m"; RESET = "\033[0m"; BOLD = "\033[1m"
passed = 0; failed = 0; warned = 0

def ok(label, detail=""):
    global passed; passed += 1
    print(f"  {GREEN}✓{RESET} {label}" + (f"  ({detail})" if detail else ""))

def fail(label, detail=""):
    global failed; failed += 1
    print(f"  {RED}✗{RESET} {label}" + (f"  — {detail}" if detail else ""))

def warn(label, detail=""):
    global warned; warned += 1
    print(f"  {YELLOW}⚠{RESET} {label}" + (f"  — {detail}" if detail else ""))

def section(title):
    print(f"\n{BOLD}{title}{RESET}")

# ── Load .env ─────────────────────────────────────────────────────────────────
section("Environment File")
dotenv_path = Path(".env")
if dotenv_path.exists():
    try:
        from dotenv import load_dotenv
        load_dotenv()
        ok(".env file found and loaded")
    except ImportError:
        # Manual parse without python-dotenv
        for line in dotenv_path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                os.environ.setdefault(k.strip(), v.strip())
        ok(".env file found (parsed manually)")
else:
    fail(".env file", "not found — run: cp .env.example .env")

provider = os.getenv("LLM_PROVIDER", "anthropic").lower()

# ── Provider detection ────────────────────────────────────────────────────────
section(f"LLM Provider: {provider.upper()}")
if provider == "anthropic":
    key = os.getenv("ANTHROPIC_API_KEY", "")
    if key and key not in ("your_key_here", ""):
        ok("ANTHROPIC_API_KEY", "set")
    else:
        fail("ANTHROPIC_API_KEY", "missing or placeholder — get one at console.anthropic.com")
    model = os.getenv("LLM_MODEL", "claude-sonnet-4-20250514")
    ok("LLM_MODEL", model)

elif provider == "llamacpp":
    base_url = os.getenv("LLAMACPP_BASE_URL", "http://localhost:8080")
    ok("LLAMACPP_BASE_URL", base_url)
    ok("LLAMACPP_MODEL", os.getenv("LLAMACPP_MODEL", "llama-3.1-8b-instruct"))
    ok("LLAMACPP_N_CTX", os.getenv("LLAMACPP_N_CTX", "4096"))
    warn("ANTHROPIC_API_KEY", "not required when LLM_PROVIDER=llamacpp (skipped)")
else:
    fail("LLM_PROVIDER", f"must be 'anthropic' or 'llamacpp', got '{provider}'")

# ── Core env vars ─────────────────────────────────────────────────────────────
section("Core Settings")
REQUIRED = {"JWT_SECRET": "API auth", "CHROMA_PERSIST_DIR": "vector store",
            "SESSION_DIR": "session storage", "LOG_LEVEL": "logging"}
for var, purpose in REQUIRED.items():
    val = os.getenv(var, "")
    if val and val not in ("change_me", "change_me_to_a_long_random_string_in_production"):
        ok(var, purpose)
    else:
        fail(var, f"missing or placeholder ({purpose})")

# ── Data directories ──────────────────────────────────────────────────────────
section("Data Directories")
for d in [os.getenv("CHROMA_PERSIST_DIR","./data/chroma"),
          os.getenv("SESSION_DIR","./data/sessions"),
          os.getenv("FAILED_FLOWS_DIR","./data/failed_flows")]:
    p = Path(d); p.mkdir(parents=True, exist_ok=True)
    try:
        tf = p / ".write_test"; tf.write_text("ok"); tf.unlink()
        ok(str(p), "writable")
    except OSError as e:
        fail(str(p), str(e))

# ── Python imports ─────────────────────────────────────────────────────────────
section("Python Packages")
PACKAGES = {"langchain": "core", "langgraph": "orchestration", "chromadb": "vector store",
            "fastapi": "REST API", "pydantic": "validation", "structlog": "logging",
            "prometheus_client": "metrics", "tenacity": "retries", "jose": "JWT auth"}
for pkg, purpose in PACKAGES.items():
    try:
        __import__(pkg); ok(pkg, purpose)
    except ImportError:
        fail(pkg, f"run: pip install {pkg}")

# Provider-specific package
if provider == "anthropic":
    try:
        import langchain_anthropic; ok("langchain-anthropic", "Anthropic LLM")
    except ImportError:
        fail("langchain-anthropic", "run: pip install langchain-anthropic")
elif provider == "llamacpp":
    try:
        import langchain_openai; ok("langchain-openai", "llama.cpp OpenAI-compat client")
    except ImportError:
        fail("langchain-openai", "run: pip install langchain-openai")

# ── Provider connectivity ──────────────────────────────────────────────────────
section("Provider Connectivity")
if provider == "anthropic":
    key = os.getenv("ANTHROPIC_API_KEY", "")
    if key and key != "your_key_here":
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=key)
            start = time.perf_counter()
            client.messages.create(model="claude-haiku-4-5-20251001", max_tokens=5,
                                   messages=[{"role":"user","content":"ping"}])
            ok("Anthropic API", f"reachable ({round((time.perf_counter()-start)*1000)}ms)")
        except Exception as e:
            fail("Anthropic API", str(e)[:80])
    else:
        warn("Anthropic API", "skipped (key not set)")
elif provider == "llamacpp":
    base_url = os.getenv("LLAMACPP_BASE_URL", "http://localhost:8080")
    try:
        import urllib.request, json
        req = urllib.request.Request(f"{base_url}/health", method="GET")
        start = time.perf_counter()
        with urllib.request.urlopen(req, timeout=3) as resp:
            latency = round((time.perf_counter()-start)*1000)
            ok(f"llama.cpp server at {base_url}", f"reachable ({latency}ms)")
    except Exception as e:
        fail(f"llama.cpp server at {base_url}",
             f"not reachable — start it first (see .env.example for the command): {str(e)[:60]}")

# ── ChromaDB ──────────────────────────────────────────────────────────────────
section("ChromaDB")
try:
    import chromadb
    client = chromadb.PersistentClient(path=os.getenv("CHROMA_PERSIST_DIR","./data/chroma"))
    cols = client.list_collections()
    ok("ChromaDB local client", f"{len(cols)} collection(s) found")
    if not cols:
        warn("Knowledge base", "empty — run: python scripts/seed_knowledge.py")
except Exception as e:
    fail("ChromaDB", str(e)[:80])

# ── Summary ────────────────────────────────────────────────────────────────────
total = passed + failed + warned
print(f"\n{'─'*50}")
print(f"  {GREEN}{passed}{RESET} passed  {RED}{failed}{RESET} failed  {YELLOW}{warned}{RESET} warnings  (of {total} checks)")
if failed > 0:
    print(f"\n  {RED}Fix the failing checks before starting the application.{RESET}")
    sys.exit(1)
else:
    print(f"\n  {GREEN}✓ All critical checks passed — ready to start!{RESET}")
    if provider == "anthropic":
        print("  Run: make run-dev")
    else:
        print(f"  Ensure llama.cpp server is running at {os.getenv('LLAMACPP_BASE_URL','http://localhost:8080')}")
        print("  Run: make run-dev")
    sys.exit(0)

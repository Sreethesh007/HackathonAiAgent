.PHONY: install test lint format run-dev run-docker clean env-check token help

# ── Variables ─────────────────────────────────────────────────────────────────
PYTHON     := python3
PIP        := pip3
APP_MODULE := src.api.main:app
TEST_DIR   := tests

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ── Setup ─────────────────────────────────────────────────────────────────────
install:  ## Install all dependencies
	$(PIP) install -e ".[dev]"
	cp -n .env.example .env || true
	@echo "✓ Dependencies installed. Fill in .env before running."

env-check:  ## Verify environment is correctly configured
	$(PYTHON) scripts/check_env.py

# ── Development ───────────────────────────────────────────────────────────────
run-dev:  ## Start API in development mode (hot-reload)
	uvicorn $(APP_MODULE) --host 0.0.0.0 --port 8000 --reload --log-level info

run-scenarios:  ## Run the three demo scenarios (requires ANTHROPIC_API_KEY)
	$(PYTHON) examples/scenarios.py

token:  ## Generate a dev JWT token  (usage: make token USER=alice)
	$(PYTHON) -c "from src.api.auth import create_access_token; print(create_access_token('$(or $(USER),dev-user)'))"

# ── Testing ───────────────────────────────────────────────────────────────────
test:  ## Run full test suite with coverage
	pytest $(TEST_DIR) -v --tb=short --cov=src --cov-report=term-missing --cov-report=xml

test-fast:  ## Run tests without coverage (faster)
	pytest $(TEST_DIR) -v --tb=short -p no:cacheprovider --no-cov

test-watch:  ## Watch mode — re-run on file changes (requires pytest-watch)
	ptw $(TEST_DIR) -- -v --tb=short --no-cov

# ── Code quality ──────────────────────────────────────────────────────────────
lint:  ## Run ruff linter
	ruff check src/ tests/ examples/

format:  ## Auto-format with black + ruff
	black src/ tests/ examples/
	ruff check --fix src/ tests/ examples/

typecheck:  ## Run mypy type checking
	mypy src/ --ignore-missing-imports

# ── Docker ────────────────────────────────────────────────────────────────────
run-docker:  ## Start full stack with Docker Compose
	docker compose up --build -d
	@echo "✓ Stack started:"
	@echo "   API       → http://localhost:8000"
	@echo "   API Docs  → http://localhost:8000/docs"
	@echo "   Chroma    → http://localhost:8001"
	@echo "   Prometheus→ http://localhost:9090"
	@echo "   Grafana   → http://localhost:3000  (admin/admin)"

stop-docker:  ## Stop all Docker services
	docker compose down

logs:  ## Tail application logs
	docker compose logs -f app

# ── Utilities ─────────────────────────────────────────────────────────────────
seed-knowledge:  ## Seed vector store with medical guidelines
	$(PYTHON) scripts/seed_knowledge.py

export-graph:  ## Export LangGraph pipeline diagram to docs/graph.md
	$(PYTHON) -c "from src.graph.pipeline import HealthcareTriageGraph; HealthcareTriageGraph().export_mermaid()"
	@echo "✓ Graph exported to docs/graph.md"

clean:  ## Remove generated files and caches
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov coverage.xml .coverage
	@echo "✓ Cleaned"

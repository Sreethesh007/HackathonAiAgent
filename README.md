<div align="center">

<img src="https://img.shields.io/badge/-%F0%9F%8F%A5%20Healthcare%20Triage%20Agent-1a1a2e?style=for-the-badge" alt="Healthcare Triage Agent"/>

# Healthcare Triage Agent

**Autonomous multi-agent AI system for real-time clinical triage**

<p>
  <a href="https://github.com/Sreethesh007/HackathonAiAgent/actions/workflows/ci.yml">
    <img src="https://github.com/Sreethesh007/HackathonAiAgent/actions/workflows/ci.yml/badge.svg" alt="Backend CI"/>
  </a>
  <a href="https://github.com/Sreethesh007/HackathonAiAgent/actions/workflows/frontend-ci.yml">
    <img src="https://github.com/Sreethesh007/HackathonAiAgent/actions/workflows/frontend-ci.yml/badge.svg" alt="Frontend CI"/>
  </a>
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/Angular-21-DD0031?logo=angular&logoColor=white" alt="Angular"/>
  <img src="https://img.shields.io/badge/FastAPI-0.111+-009688?logo=fastapi&logoColor=white" alt="FastAPI"/>
  <img src="https://img.shields.io/badge/LangGraph-Enabled-6366f1?logo=chainlink&logoColor=white" alt="LangGraph"/>
  <img src="https://img.shields.io/badge/License-MIT-22c55e" alt="License"/>
</p>

<p>
  <img src="https://img.shields.io/badge/Supabase-Auth%20%2B%20DB-3ECF8E?logo=supabase&logoColor=white" alt="Supabase"/>
  <img src="https://img.shields.io/badge/ChromaDB-Vector%20Store-orange?logo=databricks&logoColor=white" alt="ChromaDB"/>
  <img src="https://img.shields.io/badge/Prometheus-Metrics-E6522C?logo=prometheus&logoColor=white" alt="Prometheus"/>
  <img src="https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker&logoColor=white" alt="Docker"/>
</p>

> Six specialised LLM agents. One seamless pipeline. Real-time SSE streaming.
> From symptom description to clinician-reviewed recommendation — in seconds.

</div>

---

## 📋 Table of Contents

- [✨ Overview](#-overview)
- [🏗️ Architecture](#️-architecture)
  - [System Architecture](#system-architecture)
  - [Agent Pipeline](#agent-pipeline)
  - [Data Flow](#data-flow)
  - [Frontend Structure](#frontend-structure)
- [🛠️ Tech Stack](#️-tech-stack)
- [📁 Repository Structure](#-repository-structure)
- [🚀 Setup Instructions](#-setup-instructions)
  - [Prerequisites](#prerequisites)
  - [Backend](#backend-local-development)
  - [Frontend](#frontend-local-development)
  - [Docker Compose](#full-stack-with-docker-compose)
  - [Local Models (llama.cpp)](#local-models-with-llamacpp)
- [⚙️ Environment Variables](#️-environment-variables)
- [📖 Usage](#-usage)
  - [Seeding the Knowledge Base](#seeding-the-knowledge-base)
  - [API Endpoints](#api-endpoints)
  - [Example API Calls](#example-api-calls)
  - [Demo Scenarios](#demo-scenarios)
- [🧪 Testing](#-testing)
- [🔄 CI/CD](#-cicd)
- [☁️ Deployment](#️-deployment)
- [📊 Observability](#-observability)
- [🔒 Security](#-security)
- [🔧 Troubleshooting](#-troubleshooting)
- [🤝 Contributing](#-contributing)

---

## ✨ Overview

Healthcare Triage Agent is a production-grade autonomous AI system. A patient describes their symptoms through a conversational interface, and a pipeline of six specialised agents collaborates to deliver a safe, evidence-based recommendation — streamed in real-time.

```mermaid
mindmap
  root((🏥 Triage Agent))
    Patient Facing
      💬 Chat Interface
      📋 Session History
      📅 Appointments
    Clinician Facing
      📊 Analytics Dashboard
      ✅ HITL Reviews
      🗓️ Appointment Manager
    AI Pipeline
      🧠 Orchestrator
      🩺 Triage Assessment
      📚 RAG Research
      🔍 Critic Review
      📅 Scheduler
      ✍️ Synthesizer
    Infrastructure
      ⚡ FastAPI + SSE
      🗄️ ChromaDB
      🔐 Supabase Auth
      📈 Prometheus
```

### Key Capabilities

| | Feature | Description |
|---|---------|-------------|
| 🤖 | **Multi-Agent Pipeline** | 6 agents orchestrated via LangGraph StateGraph with MemorySaver checkpointing |
| 🔀 | **Dual LLM Providers** | Switch Anthropic Claude ↔ llama.cpp (local, zero-cost) with one env var |
| 📚 | **RAG Knowledge Base** | ChromaDB + 18 WHO/NICE/AHA guidelines + PDF ingestion, fully offline |
| ⚡ | **Real-time Streaming** | SSE token-by-token output with agent step events |
| 👩‍⚕️ | **HITL Safety Net** | Auto-escalate to clinician when confidence score < threshold |
| 🔐 | **Supabase Auth** | Email/password with role-based routing (patient vs. clinician) |
| 📊 | **Full Observability** | Prometheus metrics + structlog with PII auto-redaction |
| 🐳 | **Container Ready** | Multi-stage Docker builds + Docker Compose full stack |

---

## 🏗️ Architecture

### System Architecture

```mermaid
graph TB
    subgraph CLIENT["🌐 Browser Client"]
        direction TB
        LP["🏠 Landing Page"]
        AUTH["🔐 Auth Pages\nLogin · Signup · Reset"]
        PAT["👤 Patient Shell\nTriage Chat · History"]
        CLIN["👩‍⚕️ Clinician Shell\nDashboard · Reviews · Appointments"]
    end

    subgraph GATEWAY["🔀 API Gateway (Nginx)"]
        PROXY["Reverse Proxy\n/api/* → FastAPI\nStatic → Angular SPA"]
    end

    subgraph BACKEND["⚙️ Backend (FastAPI + LangGraph)"]
        direction TB
        API["🛣️ REST + SSE Endpoints"]
        PIPELINE["🔄 Agent Pipeline\nLangGraph StateGraph"]
        AUTH_SVC["🔑 Auth Service\nJWT · Supabase verify"]
        METRICS["📈 /metrics\nPrometheus"]
    end

    subgraph AGENTS["🤖 Agent Pipeline"]
        direction LR
        O["🧠 Orchestrator"] --> T["🩺 Triage"]
        T --> R["📚 Research"]
        R --> C["🔍 Critic"]
        C -->|approved| S["📅 Scheduler"]
        C -->|escalate| H["👩‍⚕️ Human Review"]
        S --> SY["✍️ Synthesizer"]
        H -->|approved| SY
    end

    subgraph DATA["🗄️ Data Layer"]
        CHROMA["🔵 ChromaDB\n18 Guidelines + PDFs\nall-MiniLM-L6-v2"]
        SUPA["🟢 Supabase\nAuth · Conversations\nAppointments"]
    end

    subgraph OBS["📊 Observability"]
        PROM["🔴 Prometheus"]
        GRAF["📊 Grafana"]
        LOGS["📝 structlog\nJSON · PII-redacted"]
    end

    CLIENT -- "HTTPS + Bearer JWT" --> GATEWAY
    GATEWAY --> BACKEND
    BACKEND --> AGENTS
    AGENTS --> DATA
    BACKEND --> OBS
    PROM --> GRAF
```

---

### Agent Pipeline

```mermaid
flowchart TD
    START(["📨 Patient Message\nReceived"]):::start

    ORCH["🧠 Orchestrator\nPlan · Route · Guard"]:::agent

    TRIAGE["🩺 Triage Agent\nABCDE Assessment\nSeverity Score 0–10\nUrgency Classification"]:::agent

    RESEARCH["📚 Research Agent\nChromaDB RAG Lookup\n18+ Clinical Guidelines\nEvidence Retrieval"]:::agent

    CRITIC{"🔍 Critic Agent\nQuality Review\nSafety Check"}:::decision

    SCHED["📅 Scheduler Agent\nSlot Availability\nAppointment Booking\nSupabase Persist"]:::agent

    HITL["👩‍⚕️ Human Review\nClinician Notified\nPipeline Paused\n⏸ HITL Pause"]:::hitl

    SYNTH["✍️ Synthesizer\nPatient-Friendly Response\nEvidence Citations\nStreamed via SSE"]:::agent

    END(["✅ Response Delivered\nto Patient"]):::finish

    START --> ORCH
    ORCH -- "route: triage" --> TRIAGE
    ORCH -- "exhausted / failed" --> SYNTH
    TRIAGE --> RESEARCH
    RESEARCH --> CRITIC

    CRITIC -- "✅ Approved +\nRoutine/Urgent" --> SCHED
    CRITIC -- "✅ Approved +\nEmergency" --> SYNTH
    CRITIC -- "⚠️ Low confidence\nscore < 0.70" --> HITL
    CRITIC -- "❌ Not approved\niterations left" --> ORCH

    HITL -- "✅ Clinician approves" --> SYNTH
    SCHED --> SYNTH
    SYNTH --> END

    classDef start fill:#6366f1,color:#fff,stroke:#4f46e5,rx:20
    classDef finish fill:#22c55e,color:#fff,stroke:#16a34a,rx:20
    classDef agent fill:#1e293b,color:#e2e8f0,stroke:#334155
    classDef decision fill:#0f172a,color:#f8fafc,stroke:#6366f1
    classDef hitl fill:#7c3aed,color:#fff,stroke:#6d28d9
```

---

### Data Flow

```mermaid
sequenceDiagram
    autonumber
    actor Patient
    participant FE as 🌐 Angular Frontend
    participant API as ⚡ FastAPI
    participant LG as 🔄 LangGraph
    participant VDB as 🔵 ChromaDB
    participant LLM as 🤖 LLM Provider
    participant DB as 🟢 Supabase

    Patient->>FE: Describe symptoms
    FE->>API: POST /triage (Bearer JWT)
    API->>DB: Verify JWT token
    DB-->>API: User role confirmed
    API->>LG: Create AgentState & invoke graph
    Note over LG: Orchestrator routes → Triage

    LG->>LLM: ABCDE assessment prompt
    LLM-->>LG: Severity score + urgency
    Note over LG: Routes → Research

    LG->>VDB: Similarity search (query)
    VDB-->>LG: Top-k clinical guidelines
    LG->>LLM: Synthesize evidence summary
    LLM-->>LG: Research result
    Note over LG: Routes → Critic

    LG->>LLM: Quality review prompt
    LLM-->>LG: approved=true, score=0.85

    alt Routine / Urgent → Book appointment
        LG->>DB: Check slot availability
        DB-->>LG: Available slots
        LG->>DB: Insert appointment
    end

    LG->>LLM: Generate patient response (stream)
    loop SSE Streaming
        LLM-->>API: Token chunk
        API-->>FE: data: {"type":"message","token":"..."}
        FE-->>Patient: Rendered incrementally
    end

    API->>DB: Save conversation turn
    API-->>FE: data: {"type":"metadata",...}
    FE-->>Patient: Appointment confirmation + severity badge
```

---

### Frontend Structure

```mermaid
graph LR
    subgraph ROUTES["🛣️ Route Tree"]
        ROOT["/"]
        ROOT --> LAND["/ → Landing"]
        ROOT --> LOGIN["/login → Auth"]
        ROOT --> SIGNUP["/signup → Auth"]
        ROOT --> PAT["/patient → Patient Shell"]
        ROOT --> CLIN["/clinician → Clinician Shell"]
    end

    subgraph PATIENT_FEAT["👤 Patient Features"]
        PAT --> TRIAGE_PAGE["Triage Chat\nSSE streaming\nSession history"]
    end

    subgraph CLIN_FEAT["👩‍⚕️ Clinician Features"]
        CLIN --> OV["Overview\nAnalytics charts"]
        CLIN --> PEND["Pending Reviews\nHITL approve/reject"]
        CLIN --> APPT["Appointments\nCalendar view"]
    end

    subgraph CORE["🔧 Core (Singleton)"]
        AUTH_SVC2["auth.service\nSupabase + signals"]
        TRIAGE_SVC["triage-api.service\nSSE + REST client"]
        NOTIF["notification.service"]
        GUARD_A["authGuard"]
        GUARD_R["roleGuard"]
        INTERCEPT["jwtInterceptor\nauto-attach Bearer"]
    end
```

---

## 🛠️ Tech Stack

### Backend

| Layer | Technology | Purpose |
|-------|-----------|---------|
| 🌐 **API** | FastAPI 0.111+ | Async REST + SSE endpoints |
| 🔄 **Orchestration** | LangGraph StateGraph | Multi-agent pipeline & routing |
| 🤖 **LLM (Cloud)** | Anthropic Claude | Production-grade reasoning |
| 🤖 **LLM (Local)** | llama.cpp OpenAI-compat | Zero-cost offline inference |
| 🔵 **Vector Store** | ChromaDB + sentence-transformers | RAG over clinical guidelines |
| 🟢 **Database** | Supabase (PostgreSQL) | Conversations + appointments |
| 🔑 **Auth** | Supabase Auth + JWT HS256 | User sessions + API auth |
| ✅ **Validation** | Pydantic v2 | Strict typed state models |
| 🚦 **Rate Limiting** | SlowAPI | Per-IP request throttling |
| 📝 **Logging** | structlog | JSON + PII redaction |
| 📈 **Metrics** | prometheus-client | Counters, histograms, gauges |
| 🔁 **Resilience** | tenacity | Retry with backoff |

### Frontend

| Layer | Technology | Purpose |
|-------|-----------|---------|
| 🅰️ **Framework** | Angular 21 | Standalone components + signals |
| 🎨 **UI** | Angular Material 21 | Component library + theming |
| 🔐 **Auth** | Supabase JS SDK | Session persistence + OAuth ready |
| 📊 **Charts** | Chart.js + ng2-charts | Clinician analytics |
| ⚡ **Streaming** | Fetch API + ReadableStream | SSE event parsing |
| 🎭 **Styling** | SCSS + custom design system | Theming + animations |
| 🧪 **Testing** | Vitest + jsdom | Unit tests |
| 🐳 **Serving** | Nginx 1.27 Alpine | SPA routing + API proxy |

### Infrastructure

| Component | Technology |
|-----------|-----------|
| 🐳 **Containers** | Docker multi-stage builds |
| 🔀 **Proxy** | Nginx (SPA + API reverse proxy) |
| 📊 **Monitoring** | Prometheus + Grafana |
| 🔄 **CI/CD** | GitHub Actions (2 workflows) |
| ☁️ **Deploy** | Azure Web App (BE) · Docker Compose |

---

## 📁 Repository Structure

```
healthcare-triage-agent/
│
├── 📂 .github/workflows/
│   ├── ci.yml                    # Backend: lint → test → coverage → Docker
│   └── frontend-ci.yml           # Frontend: test → build → Docker image
│
├── 📂 src/                       # Python backend
│   ├── 📂 api/
│   │   ├── main.py               # FastAPI app, SSE streaming, rate limiting
│   │   ├── auth.py               # JWT + Supabase token verification
│   │   ├── schemas.py            # Pydantic request/response models
│   │   └── conversation_store.py # Supabase conversation persistence
│   ├── 📂 agents/
│   │   ├── orchestrator.py       # Plans, routes, guards max iterations
│   │   ├── triage_agent.py       # ABCDE assessment + severity scoring
│   │   ├── research_agent.py     # ChromaDB RAG retrieval
│   │   ├── scheduler_critic_agents.py  # Booking + quality review
│   │   └── synthesizer.py        # Response generation + HITL node
│   ├── 📂 graph/
│   │   └── pipeline.py           # LangGraph StateGraph wiring
│   ├── 📂 llm/
│   │   └── provider.py           # LLM factory (Anthropic / llama.cpp)
│   ├── 📂 memory/
│   │   └── retriever.py          # ChromaDB LangChain wrapper
│   ├── 📂 tools/
│   │   └── clinical_tools.py     # Symptom lookup, severity scale, booking
│   ├── 📂 observability/
│   │   ├── logging.py            # structlog + PII redaction
│   │   └── metrics.py            # Prometheus counters/histograms/gauges
│   ├── agent_state.py            # Pydantic v2 shared AgentState model
│   ├── config.py                 # Pydantic settings (from .env)
│   └── db.py                     # Supabase appointment database
│
├── 📂 frontend/                  # Angular 21 SPA
│   ├── 📂 src/app/
│   │   ├── core/                 # Guards, interceptors, services, models
│   │   ├── features/             # auth/ patient/ clinician/ landing/
│   │   └── shared/               # Components, pipes, directives, animations
│   ├── Dockerfile                # Multi-stage: Node 20 → Nginx 1.27
│   └── nginx.conf                # SPA routing + /api proxy
│
├── 📂 monitoring/
│   └── prometheus.yml            # 15s scrape config
│
├── 📂 scripts/
│   ├── seed_knowledge.py         # Seed ChromaDB (18 guidelines + PDFs)
│   ├── check_env.py              # Pre-flight environment checker
│   ├── download_model.py         # GGUF model downloader
│   └── migrate_to_supabase.py   # Migration helper
│
├── 📂 tests/
│   ├── test_all.py               # 500+ line test suite (unit + integration)
│   └── test_provider.py          # LLM provider tests
│
├── 📂 examples/
│   └── scenarios.py              # 3 demo scenarios (emergency/routine/HITL)
│
├── 📂 data/                      # Runtime data (gitignored)
│   ├── chroma/                   # ChromaDB persistent storage
│   ├── sessions/                 # LangGraph session files
│   └── failed_flows/             # Failed pipeline state dumps
│
├── Makefile                      # 20+ automation targets
├── pyproject.toml                # Python deps + tool config
├── .env.example                  # All env vars documented
└── .gitignore
```

---

## 🚀 Setup Instructions

### Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| 🐍 Python | `3.11+` | Use pyenv or official installer |
| 📦 Node.js | `20+` | LTS recommended |
| 📦 npm | `11+` | Included with Node |
| 🐙 Git | `2.40+` | |
| 🛠️ Make | `4.0+` | Required for automation targets |
| 🐳 Docker | `24+` | Optional — for containerised stack |

> 💡 **Windows Users**: You will need `make` installed. The easiest way is via [Chocolatey](https://chocolatey.org/): `choco install make`. Alternatively, use WSL (Windows Subsystem for Linux) or Git Bash. Mac/Linux users typically have `make` pre-installed (`brew install make` or `apt install make` if missing).

---

### Backend (Local Development)

```bash
# 1. Clone
git clone https://github.com/Sreethesh007/HackathonAiAgent.git
cd HackathonAiAgent

# 2. Virtual environment
python -m venv venv
source venv/bin/activate        # macOS/Linux
venv\Scripts\activate           # Windows

# 3. Install (with dev extras)
pip install -e ".[dev]"

# 4. Configure environment
cp .env.example .env
# ✏️  Edit .env — minimum required:
#     ANTHROPIC_API_KEY, JWT_SECRET, SUPABASE_URL, SUPABASE_KEY

# 5. Pre-flight check
python scripts/check_env.py

# 6. Seed knowledge base (first run only)
python scripts/seed_knowledge.py

# 7. Start API (hot-reload)
make run-dev
# or: uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

| Endpoint | URL |
|----------|-----|
| 🌐 API | http://localhost:8000 |
| 📄 Swagger UI | http://localhost:8000/docs |
| 📄 ReDoc | http://localhost:8000/redoc |
| 📈 Metrics | http://localhost:8000/metrics |

---

### Frontend (Local Development)

```bash
cd frontend

# 1. Configure environment
cp .env.example .env
# ✏️  Edit .env — set SUPABASE_URL and SUPABASE_KEY

# 2. Install dependencies
npm install

# 3. Start dev server (proxies /api/* → localhost:8000)
npm start
```

> 💡 `npm start` runs `npm run config && ng serve`. The config script reads `frontend/.env` and generates `environment.ts`.

Frontend available at **http://localhost:4200**

---

### Full Stack with Docker Compose

```bash
docker compose up --build -d
```

| Service | URL | Credentials |
|---------|-----|-------------|
| ⚡ FastAPI | http://localhost:8000 | Bearer JWT |
| 🔵 ChromaDB | http://localhost:8001 | — |
| 🔴 Prometheus | http://localhost:9090 | — |
| 📊 Grafana | http://localhost:3000 | `admin` / `admin` |

```bash
docker compose logs -f app   # Follow API logs
docker compose down          # Tear down
```

---

### Local Models with llama.cpp

Run fully offline — no API keys required:

```bash
# 1. Build llama.cpp
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp && cmake -B build && cmake --build build -j$(nproc)

# 2. Download a model
python scripts/download_model.py --model llama3.1-8b-q4

# 3. Start llama.cpp server
./build/bin/llama-server \
  -m models/llama-3.1-8b-instruct.Q4_K_M.gguf \
  --host 0.0.0.0 --port 8080 \
  --n-gpu-layers 0 --threads 4 --ctx-size 4096

# 4. Switch provider
# In .env: LLM_PROVIDER=llamacpp

# 5. Verify + start
make check-llamacpp && make run-dev
```

**Recommended models by available RAM:**

| Model | RAM | Quality |
|-------|-----|---------|
| `phi-3-mini-4k-instruct.Q4_K_M.gguf` | 3 GB | ⭐⭐ |
| `llama-3.1-8b-instruct.Q4_K_M.gguf` | 6 GB | ⭐⭐⭐ |
| `llama-3.1-8b-instruct.Q8_0.gguf` | 8 GB | ⭐⭐⭐⭐ |
| `mistral-7b-instruct-v0.3.Q4_K_M.gguf` | 5 GB | ⭐⭐⭐ |

---

## ⚙️ Environment Variables

All variables are documented in [`.env.example`](.env.example). Copy it to `.env` to get started.

<details>
<summary><b>🤖 LLM Provider</b></summary>

| Variable | Description | Default |
|----------|-------------|---------|
| `LLM_PROVIDER` | `anthropic` or `llamacpp` | `anthropic` |
| `ANTHROPIC_API_KEY` | Anthropic API key | — |
| `LLM_MODEL` | Anthropic model name | `claude-sonnet-4-20250514` |
| `LLAMACPP_BASE_URL` | llama.cpp server URL | `http://localhost:8080` |
| `LLAMACPP_MODEL` | Local model display name | `llama-3.1-8b-instruct` |
| `LLAMACPP_N_CTX` | Context window | `4096` |
| `LLM_MAX_TOKENS` | Max output tokens | `2048` |
| `LLM_TEMPERATURE` | Sampling temperature | `0.1` |

</details>

<details>
<summary><b>🔵 Vector Store & Memory</b></summary>

| Variable | Description | Default |
|----------|-------------|---------|
| `CHROMA_PERSIST_DIR` | ChromaDB storage path | `./data/chroma` |
| `CHROMA_COLLECTION_NAME` | Collection name | `medical_guidelines` |
| `SESSION_DIR` | Session state path | `./data/sessions` |
| `SESSION_TTL_SECONDS` | Session time-to-live | `7200` |
| `MEMORY_WINDOW_SIZE` | Conversation window size | `10` |

</details>

<details>
<summary><b>🔄 Agent Pipeline</b></summary>

| Variable | Description | Default |
|----------|-------------|---------|
| `MAX_AGENT_ITERATIONS` | Max pipeline loop iterations | `10` |
| `MAX_FLOW_DURATION_SECONDS` | Pipeline hard timeout | `120` |
| `AGENT_RETRY_ATTEMPTS` | LLM retries per agent | `3` |
| `HUMAN_APPROVAL_THRESHOLD` | Critic score → HITL trigger | `0.70` |

</details>

<details>
<summary><b>🔑 API & Auth</b></summary>

| Variable | Description | Default |
|----------|-------------|---------|
| `API_HOST` | Bind address | `0.0.0.0` |
| `API_PORT` | Port | `8000` |
| `CORS_ORIGINS` | Allowed origins (comma-sep) | `http://localhost:3000` |
| `RATE_LIMIT_PER_MINUTE` | Requests/min per IP | `10` |
| `JWT_SECRET` | JWT signing secret ⚠️ **change in prod** | `change_me` |
| `JWT_ALGORITHM` | JWT algorithm | `HS256` |
| `JWT_EXPIRE_MINUTES` | Token TTL | `60` |
| `SUPABASE_URL` | Supabase project URL | — |
| `SUPABASE_KEY` | Supabase anon key | — |

</details>

<details>
<summary><b>📊 Observability</b></summary>

| Variable | Description | Default |
|----------|-------------|---------|
| `LOG_LEVEL` | Logging verbosity | `INFO` |
| `ENVIRONMENT` | `development` or `production` | `development` |
| `LANGCHAIN_TRACING_V2` | LangSmith tracing | `false` |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | OpenTelemetry endpoint | — |

</details>

---

## 📖 Usage

### Seeding the Knowledge Base

The system needs a seeded ChromaDB collection to perform evidence-based triage. The seeder ships with **18 built-in clinical guidelines** (WHO, NICE, AHA) across emergency, urgent, and routine categories.

```bash
python scripts/seed_knowledge.py         # Seed (skip existing)
python scripts/seed_knowledge.py --reset # Wipe and reseed

make seed-knowledge                      # Makefile shortcut
```

> 📄 **Add custom guidelines**: Drop PDF files into `data/knowledge/` and re-run the seeder. It automatically chunks (800 chars, 150 char overlap) and embeds them using `all-MiniLM-L6-v2`.

---

### API Endpoints

```mermaid
graph LR
    subgraph TRIAGE["🩺 Triage"]
        T1["POST /triage\nStart session SSE"]
        T2["POST /triage/:id/continue\nContinue / HITL"]
        T3["GET /triage/:id/status\nInspect state"]
    end

    subgraph SESSION["📋 Sessions"]
        S1["GET /sessions\nPatient history"]
        S2["POST /api/conversations\nSave turn"]
        S3["GET /api/conversations/:id\nGet history"]
        S4["DELETE /api/conversations/:id\nDelete session"]
    end

    subgraph CLINICIAN["👩‍⚕️ Clinician"]
        C1["GET /clinician/pending\nHITL reviews"]
        C2["GET /clinician/appointments\nAll bookings"]
        C3["GET /clinician/check-slot\nSlot availability"]
    end

    subgraph SYSTEM["⚙️ System"]
        SY1["GET /health\nLiveness probe"]
        SY2["GET /health/llm\nLLM deep check"]
        SY3["GET /health/knowledge\nVector store check"]
        SY4["GET /metrics\nPrometheus"]
        SY5["GET /docs\nSwagger UI"]
    end
```

**SSE Event Types** (from `/triage` and `/triage/:id/continue`):

| Event | Description |
|-------|-------------|
| `step_start` | Agent node started (`triage`, `research`, …) |
| `thinking` | LLM tokens from intermediate agents |
| `message` | Final synthesizer tokens (patient response) |
| `step_content` | Per-agent reasoning summary |
| `metadata` | Final session data (severity, urgency, appointment) |
| `error` | Error details |

---

### Example API Calls

#### Start a Triage Session

```bash
# Obtain a token
TOKEN=$(python -c "from src.api.auth import create_access_token; print(create_access_token('patient-001'))")

# Start triage — SSE stream
curl -N \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "I have severe chest pain radiating to my left arm. I am sweating and feel nauseous."}' \
  http://localhost:8000/triage

# Example SSE response stream:
# data: {"type":"step_start","agent":"triage","message":"Starting triage assessment"}
# data: {"type":"thinking","token":"Assessing"}
# data: {"type":"message","token":"Based on your symptoms..."}
# data: {"type":"metadata","severity_score":9,"urgency_level":"emergency","appointment_booked":false}
```

#### Continue / Approve HITL

```bash
# Follow-up message
curl -N -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "The pain started 20 minutes ago", "patient_id": "patient-001"}' \
  http://localhost:8000/triage/{session_id}/continue

# Clinician approves HITL
curl -N -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"human_approval": true}' \
  http://localhost:8000/triage/{session_id}/continue
```

#### Health Check

```bash
curl http://localhost:8000/health
# → {"status":"ok","version":"1.0.0","llm_provider":"anthropic","pipeline_ready":true}

curl http://localhost:8000/health/knowledge
# → {"status":"ok","document_count":18,"collection":"medical_guidelines"}
```

---

### Demo Scenarios

```bash
make run-scenarios   # or: python examples/scenarios.py
```

```mermaid
timeline
    title Demo Scenario Outcomes
    section 🚨 Emergency
        Chest pain + sweating : Severity 9/10
                              : urgency = EMERGENCY
                              : "Call 112 immediately"
    section 📅 Routine
        BP follow-up, stable  : Severity 2/10
                              : urgency = ROUTINE
                              : Appointment booked
    section ⏸ HITL Escalation
        Persistent headaches  : Severity 5/10
                              : Low confidence → HITL
                              : Clinician approves → response
```

**Clinician demo login** (frontend only): `clinician@gmail.com` / `clinician`

---

## 🧪 Testing

### Coverage Targets

```mermaid
xychart-beta
    title "Test Coverage Targets (%)"
    x-axis ["agent_state", "clinical_tools", "agents/*", "pipeline", "api/*"]
    y-axis "Coverage %" 0 --> 100
    bar [100, 95, 85, 80, 80]
```

### Test Suite Overview

The `tests/test_all.py` suite (500+ lines) covers:

| Stage | Class | What's tested |
|-------|-------|---------------|
| 1 | `TestAgentState` | Instantiation, PII redaction, serialization, iteration guards |
| 2 | `TestClinicalTools` | Symptom lookup, severity scale, appointment booking |
| 3 | `TestTriageAgent` | Assessment, emergency override, LLM failure fallback |
| 4 | `TestResearchAgent` | Vector store retrieval, built-in fallback |
| 5 | `TestOrchestratorAgent` | Routing, max iterations, failure detection |
| 6 | `TestCriticAgent` | Approval, misclassification, failure → HITL |
| 7 | `TestPipelineIntegration` | End-to-end with mocked LLMs, loop termination |
| 8 | `TestAuth` | JWT creation, decoding, expiration |

```bash
make test           # Full suite + coverage report
make test-fast      # No coverage (faster)
make test-watch     # Re-run on file changes
make lint           # ruff check
make format         # black + ruff fix
make typecheck      # mypy
```

---

## 🔄 CI/CD

```mermaid
flowchart LR
    subgraph PUSH["📤 Push / PR"]
        GIT["git push\nmain or develop"]
    end

    subgraph BACKEND_CI["🐍 Backend CI"]
        direction TB
        B1["⬇️ Setup Python 3.11\npip cache"] --> B2["📦 pip install -e dev"]
        B2 --> B3["🔍 ruff check"] --> B4["🧪 pytest + coverage"]
        B4 --> B5{"≥ 40% ?"}
        B5 -- "✅ pass" --> B6["📊 Codecov upload"]
        B6 --> B7["🐳 Docker build verify"]
        B5 -- "❌ fail" --> FAIL["🚨 CI FAIL"]
    end

    subgraph FRONTEND_CI["🅰️ Frontend CI"]
        direction TB
        F1["⬇️ Setup Node 20\nnpm cache"] --> F2["📦 npm ci"]
        F2 --> F3["🧪 ng test"] --> F4["🏗️ ng build --prod"]
        F4 --> F5["🐳 Docker image build"]
        F5 --> F6["📤 Upload dist artifact\n7-day retention"]
    end

    GIT --> BACKEND_CI
    GIT --> FRONTEND_CI
```

---

## ☁️ Deployment

### Deployment Topology

```mermaid
graph TB
    subgraph PROD["🌍 Production"]
        direction LR
        subgraph STATIC["📡 Static Hosting"]
            FE_HOST["🌐 Frontend\nAngular SPA"]
        end
        subgraph AZURE["☁️ Azure"]
            WEBAPP["🔷 Azure Web App\nFastAPI Container\nACR image"]
            ACI["📦 Azure Container\nInstances\nChromaDB"]
        end
        STATIC -- "HTTPS /api/*" --> AZURE
    end

    subgraph LOCAL["🖥️ Local / Dev"]
        DC["🐳 Docker Compose\nAPI + ChromaDB\n+ Prometheus + Grafana"]
    end
```

### Docker Multi-Stage Build

```dockerfile
# Frontend: Node 20 → Nginx 1.27
FROM node:20-alpine AS builder    # Build Angular AOT bundle
FROM nginx:1.27-alpine AS runtime # Serve + proxy /api/*
```

### Deploy Commands

```bash
# Production Angular build
cd frontend && npx ng build --configuration production

# Full stack (local)
docker compose up --build -d

# Backend → Azure Web App
# 1. Push image to ACR
# 2. Point Web App to ACR image
# 3. Set all .env vars in App Service config
# 4. Set ENVIRONMENT=production (enables JSON logs + PII redaction)
```

---

## 📊 Observability

### Metrics Overview

```mermaid
graph LR
    API["⚡ FastAPI\nGET /metrics"] --> PROM["🔴 Prometheus\nScrapes every 15s"]
    PROM --> GRAF["📊 Grafana\nDashboards"]

    subgraph METRIC_TYPES["Available Metrics"]
        M1["agent_calls_total\nCounter · agent, status"]
        M2["agent_latency_seconds\nHistogram · agent"]
        M3["active_sessions\nGauge"]
        M4["flow_completions_total\nCounter · urgency_level"]
        M5["human_reviews_requested_total\nCounter"]
        M6["api_request_latency_seconds\nHistogram · endpoint"]
        M7["llm_tokens_total\nCounter · agent, token_type"]
    end
```

### Key PromQL Queries

```promql
# ── Request Rate ──────────────────────────────────────────────────
rate(api_requests_total[5m])

# ── p95 API Latency ───────────────────────────────────────────────
histogram_quantile(0.95, rate(api_request_latency_seconds_bucket[5m]))

# ── Agent Error Rate ──────────────────────────────────────────────
rate(agent_calls_total{status="error"}[5m])
  / rate(agent_calls_total[5m])

# ── Triage Completions by Urgency ─────────────────────────────────
sum by (urgency_level) (flow_completions_total)

# ── HITL Escalation Rate ──────────────────────────────────────────
rate(human_reviews_requested_total[1h])

# ── LLM Token Cost by Agent ───────────────────────────────────────
sum by (agent) (rate(llm_tokens_total[1h]))
```

### Structured Logging

| Environment | Format | PII |
|-------------|--------|-----|
| `development` | Colourised console | Plain text |
| `production` | JSON (one line per event) | SHA-256 hashed |

Fields auto-redacted in production: `patient_id`, `current_input`, `message_content`, `patient_name`

---

## 🔒 Security

```mermaid
graph TD
    REQ["🌐 Incoming Request"] --> NGINX["🔀 Nginx\nTLS termination\nSecurity headers"]
    NGINX --> RATE["🚦 SlowAPI\nRate limit 10 req/min/IP"]
    RATE --> CORS["🔐 CORS check\nExplicit allowlist"]
    CORS --> JWT_CHK["🔑 JWT verify\nHS256 + Supabase confirm"]
    JWT_CHK -->|"✅ valid"| HANDLER["📋 Route handler"]
    JWT_CHK -->|"❌ invalid"| E401["401 Unauthorized"]
    HANDLER --> RLS["🟢 Supabase RLS\nRow-level security\nData isolation"]
```

**Checklist for production deployments:**

- [ ] 🔑 Rotate `JWT_SECRET` — use `python -c "import secrets; print(secrets.token_urlsafe(48))"`
- [ ] 🟢 Enable Supabase RLS on `conversations` and `appointments` tables
- [ ] 🌐 Set `CORS_ORIGINS` to your exact frontend domain — never use `*`
- [ ] 🔒 Terminate TLS at load balancer or Nginx — never expose API over plain HTTP
- [ ] 📝 Set `ENVIRONMENT=production` to enable JSON logging + PII redaction
- [ ] 🚫 Remove mock clinician bypass (`clinician@gmail.com`) in production auth code
- [ ] 📁 Keep GGUF models outside web-accessible directories
- [ ] 🙈 Verify `.env` is in `.gitignore` — never commit secrets

---

## 🔧 Troubleshooting

<details>
<summary><b>🔴 Environment / Startup Issues</b></summary>

| Symptom | Fix |
|---------|-----|
| `.env` file not found | `cp .env.example .env` and fill values |
| `ANTHROPIC_API_KEY` missing | Get one at [console.anthropic.com](https://console.anthropic.com) |
| `Invalid LLM configuration` | `python scripts/check_env.py` |
| `JWT_SECRET` is placeholder | Generate: `python -c "import secrets; print(secrets.token_urlsafe(32))"` |
| `503 Pipeline not ready` | Wait for startup logs — ChromaDB initialises async |

</details>

<details>
<summary><b>🔵 ChromaDB / Knowledge Base</b></summary>

| Symptom | Fix |
|---------|-----|
| `knowledge_base_empty` warning | `python scripts/seed_knowledge.py --reset` |
| `PersistentClient` errors | Ensure `./data/chroma/` exists and is writable |
| `sentence-transformers` not found | `pip install sentence-transformers` |
| Embedding dimension mismatch | `seed_knowledge.py --reset` (recreates collection) |

</details>

<details>
<summary><b>🤖 llama.cpp Issues</b></summary>

| Symptom | Fix |
|---------|-----|
| Server not reachable | `make check-llamacpp` — ensure server is started first |
| Slow inference | Lower `LLAMACPP_N_CTX`, raise `LLAMACPP_N_THREADS` |
| Out of memory | Use a smaller quant: `phi-3-mini-4k-instruct.Q4_K_M.gguf` (3 GB) |
| Model file not found | `python scripts/download_model.py --list` |

</details>

<details>
<summary><b>🐳 Docker Issues</b></summary>

| Symptom | Fix |
|---------|-----|
| Port 8000 in use | Change `API_PORT` in `.env` and update compose |
| Port 3000 conflict (Grafana) | Edit port mapping in `docker-compose.yml` |
| ARM build fails | `docker buildx create --use` |
| ChromaDB permission error | `chmod -R 777 ./data/chroma` |

</details>

<details>
<summary><b>🌐 Frontend / Auth Issues</b></summary>

| Symptom | Fix |
|---------|-----|
| `/api/*` returns 502 | Ensure backend on port 8000; check `proxy.conf.json` |
| Supabase auth errors | Verify `SUPABASE_URL` + `SUPABASE_KEY` in `frontend/.env` |
| CORS errors | Add frontend URL to `CORS_ORIGINS` in backend `.env` |
| SSE stream cuts off | Raise `proxy_read_timeout` in `nginx.conf`; check firewalls |
| `environment.ts` has wrong values | `npm run config` (reads `frontend/.env`) |
| `401` on all API calls | Re-login — token expired; check `JWT_EXPIRE_MINUTES` |

</details>

---

## 🤝 Contributing

Contributions are welcome!

```bash
# 1. Fork + branch from develop
git checkout -b feature/my-improvement

# 2. Install everything
pip install -e ".[dev]" && cd frontend && npm install

# 3. Develop + test
make test && cd frontend && npm test

# 4. Lint + format
make lint && make format

# 5. Open PR against main
```

### Makefile Reference

```bash
make help              # List all targets
make install           # Install all dependencies
make run-dev           # Start API with hot-reload
make test              # Tests + coverage
make test-fast         # Tests (no coverage)
make lint              # ruff linter
make format            # black + ruff fix
make typecheck         # mypy
make seed-knowledge    # Seed vector store
make token USER=alice  # Generate dev JWT
make run-scenarios     # Run demo scenarios
make export-graph      # Export pipeline diagram → docs/graph.md
make clean             # Remove caches + generated files
```

---

<div align="center">


[![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-6366f1?logo=chainlink&logoColor=white)](https://langchain-ai.github.io/langgraph/)
[![Angular](https://img.shields.io/badge/Angular-DD0031?logo=angular&logoColor=white)](https://angular.dev/)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-orange?logo=databricks&logoColor=white)](https://www.trychroma.com/)
[![Supabase](https://img.shields.io/badge/Supabase-3ECF8E?logo=supabase&logoColor=white)](https://supabase.com/)


</div>

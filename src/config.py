"""
Centralised settings — loaded once at startup from environment variables / .env file.
Access anywhere with:  from src.config import settings
"""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── LLM Provider ───────────────────────────────────────────────────────
    # Switch between providers with a single env var:
    #   LLM_PROVIDER=anthropic   → Anthropic API (default)
    #   LLM_PROVIDER=llamacpp    → local llama.cpp server (zero API cost)
    llm_provider: str = "anthropic"          # "anthropic" | "llamacpp"

    # Anthropic settings (used when llm_provider=anthropic)
    anthropic_api_key: str = ""
    llm_model: str = "claude-sonnet-4-20250514"

    # llama.cpp settings (used when llm_provider=llamacpp)
    # Run the llama.cpp server with:
    #   ./llama-server -m models/llama-3.1-8b-instruct.gguf --port 8080
    llamacpp_base_url: str = "http://localhost:8080"
    llamacpp_model: str = "llama-3.1-8b-instruct"   # display name only
    nvidia_api_key: str = ""
    llamacpp_n_ctx: int = 4096          # context window (match your .gguf)
    llamacpp_n_threads: int = 4         # CPU threads for inference
    llamacpp_n_gpu_layers: int = 0      # 0 = CPU only; >0 = offload to GPU

    # Shared LLM settings (apply to both providers)
    llm_max_tokens: int = 2048
    llm_temperature: float = 0.1

    # Vector Store
    chroma_persist_dir: Path = Path("./data/chroma")
    chroma_collection_name: str = "medical_guidelines"
    # Embedding model — "all-MiniLM-L6-v2" runs fully offline (no API key needed).
    # Switch to "text-embedding-3-small" and set embedding_provider=openai for cloud.
    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_provider: str = "sentence_transformers"  # "sentence_transformers" | "openai"
    chroma_n_results: int = 5  # top-k documents returned per similarity search

    # Session Memory
    session_dir: Path = Path("./data/sessions")
    session_ttl_seconds: int = 7200
    memory_window_size: int = 10

    # Agent Pipeline
    max_agent_iterations: int = 10
    max_flow_duration_seconds: int = 120
    agent_retry_attempts: int = 3
    human_approval_threshold: float = 0.70

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_workers: int = 4
    cors_origins: str = "http://localhost:3000"
    rate_limit_per_minute: int = 10

    # Auth
    jwt_secret: str = "change_me"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60

    # Observability
    log_level: str = "INFO"
    environment: str = "development"
    otel_exporter_otlp_endpoint: str = ""
    langchain_tracing_v2: bool = False
    langchain_api_key: str = ""

    # Failed flows
    failed_flows_dir: Path = Path("./data/failed_flows")

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",")]

    @property
    def using_llamacpp(self) -> bool:
        return self.llm_provider.lower() == "llamacpp"

    @property
    def using_anthropic(self) -> bool:
        return self.llm_provider.lower() == "anthropic"

    def validate_llm_config(self) -> list[str]:
        """Return list of config problems (empty = all good)."""
        issues = []
        if self.using_anthropic and not self.anthropic_api_key:
            issues.append("ANTHROPIC_API_KEY is required when LLM_PROVIDER=anthropic")
        if self.using_llamacpp and not self.llamacpp_base_url:
            issues.append("LLAMACPP_BASE_URL is required when LLM_PROVIDER=llamacpp")
        if self.llm_provider not in ("anthropic", "llamacpp"):
            issues.append(f"LLM_PROVIDER must be 'anthropic' or 'llamacpp', got '{self.llm_provider}'")
        return issues

    def ensure_dirs(self) -> None:
        """Create required local directories on startup."""
        for d in [self.chroma_persist_dir, self.session_dir, self.failed_flows_dir]:
            d.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    return Settings()


# Module-level singleton
settings = get_settings()

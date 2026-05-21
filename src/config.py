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

    # LLM
    anthropic_api_key: str = ""
    llm_model: str = "claude-sonnet-4-20250514"
    llm_max_tokens: int = 2048
    llm_temperature: float = 0.1

    # Vector Store
    chroma_persist_dir: Path = Path("./data/chroma")
    chroma_collection_name: str = "medical_guidelines"
    embedding_model: str = "text-embedding-3-small"

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

    def ensure_dirs(self) -> None:
        """Create required local directories on startup."""
        for d in [self.chroma_persist_dir, self.session_dir, self.failed_flows_dir]:
            d.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    return Settings()


# Module-level singleton
settings = get_settings()

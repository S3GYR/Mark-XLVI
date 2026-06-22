"""Type-safe settings using pydantic-settings."""

from __future__ import annotations

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from jarvis.config.paths import CACHE_DIR, CONFIG_DIR, DATA_DIR


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env files."""

    model_config = SettingsConfigDict(
        env_prefix="JARVIS_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # General
    app_name: str = "JARVIS"
    debug: bool = False
    log_level: str = "INFO"

    # LLM
    llm_provider: str = "gemini"
    llm_model: str = "gemini/gemini-2.5-flash"
    llm_fallback_model: str | None = None
    llm_api_key: SecretStr | None = None
    llm_temperature: float = Field(0.7, ge=0.0, le=2.0)
    llm_max_tokens: int | None = None

    # Audio
    audio_channels: int = 1
    audio_send_sample_rate: int = 16000
    audio_receive_sample_rate: int = 24000
    audio_chunk_size: int = 1024
    audio_device_index: int | None = None

    # Dashboard
    dashboard_host: str = "127.0.0.1"
    dashboard_port: int = 8000
    dashboard_max_upload_mb: int = 500
    dashboard_auth_token_ttl: int = 3600
    dashboard_auto_firewall: bool = False

    # Security
    require_confirmation: bool = True
    sandbox_enabled: bool = True

    # Memory
    memory_backend: str = "postgres"  # postgres, json
    postgres_url: str | None = None
    vector_dim: int = 768
    memory_max_chars: int = 4000

    # Embeddings
    embedding_provider: str = "sentence-transformers"  # sentence-transformers, litellm, mock
    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_device: str = "cpu"  # cpu, cuda, mps
    embedding_fallback_to_mock: bool = True

    # Paths
    data_dir: str = str(DATA_DIR)
    config_dir: str = str(CONFIG_DIR)
    cache_dir: str = str(CACHE_DIR)

    @property
    def data_path(self) -> str:
        return self.data_dir

    @property
    def config_path(self) -> str:
        return self.config_dir


_settings: Settings | None = None


def get_settings() -> Settings:
    """Return the singleton settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reload_settings() -> Settings:
    """Reload settings from environment."""
    global _settings
    _settings = Settings()
    return _settings

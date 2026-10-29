"""App settings, loaded from environment variables / the .env file."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Every field can be overridden by an env var of the same name (case-insensitive)."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "DocChat API"
    # Origins allowed to call the API from a browser (the Vite dev server by default)
    cors_origins: list[str] = ["http://localhost:5173"]

    # Chunking: size and overlap are in characters
    chunk_size: int = 800
    chunk_overlap: int = 150

    # Embeddings + vector store
    embedding_model: str = "all-MiniLM-L6-v2"
    chroma_dir: Path = Path("data/chroma")

    # Uploads: reject anything bigger before parsing it
    max_upload_mb: int = 20


@lru_cache
def get_settings() -> Settings:
    """Read settings once and reuse them, instead of re-reading .env on every call."""
    return Settings()

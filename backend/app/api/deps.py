"""Shared FastAPI dependencies. Tests override these to inject fakes."""

from functools import lru_cache, partial
from typing import Annotated

from fastapi import Depends

from app.core.config import Settings, get_settings
from app.services.embeddings import embed_texts
from app.services.llm import generate
from app.services.rag import GenerateFn
from app.services.vector_store import VectorStore


@lru_cache
def get_vector_store() -> VectorStore:
    """One store per process, created on first use so /health never loads the model."""
    settings = get_settings()
    embed = partial(embed_texts, model_name=settings.embedding_model)
    return VectorStore(settings.chroma_dir, embed)


def get_generate(settings: Annotated[Settings, Depends(get_settings)]) -> GenerateFn:
    return partial(
        generate,
        url=settings.ollama_url,
        model=settings.ollama_model,
        timeout=settings.llm_timeout_seconds,
    )


SettingsDep = Annotated[Settings, Depends(get_settings)]
VectorStoreDep = Annotated[VectorStore, Depends(get_vector_store)]
GenerateDep = Annotated[GenerateFn, Depends(get_generate)]

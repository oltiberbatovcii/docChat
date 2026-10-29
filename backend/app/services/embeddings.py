"""Turn text into vectors with a local sentence-transformers model."""

from functools import lru_cache
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sentence_transformers import SentenceTransformer


@lru_cache
def _load_model(model_name: str) -> "SentenceTransformer":
    """Load the model once per process; loading takes seconds, encoding takes milliseconds."""
    # Imported here, not at the top: it pulls in PyTorch (slow, large), which only
    # embedding needs. App startup, /health and the test suite stay fast without it.
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(model_name)


def embed_texts(texts: list[str], model_name: str) -> list[list[float]]:
    """Return one unit-length vector per text, so cosine similarity is just a dot product."""
    vectors = _load_model(model_name).encode(texts, normalize_embeddings=True)
    return vectors.tolist()

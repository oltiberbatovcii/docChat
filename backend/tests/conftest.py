"""Shared test helpers: fake PDFs, a fake embedder, and a temporary vector store."""

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from fpdf import FPDF

from app.api.deps import get_vector_store
from app.main import app
from app.services.vector_store import VectorStore

VOCABULARY = ["venus", "jupiter", "mars", "comet"]


def fake_embed(texts: list[str]) -> list[list[float]]:
    """Count vocabulary words: similar wording -> similar vectors, with no model download.

    The constant 1.0 keeps vectors non-zero (cosine similarity is undefined for zero vectors).
    """
    return [[float(text.lower().count(word)) for word in VOCABULARY] + [1.0] for text in texts]


def make_pdf_bytes(pages: list[str]) -> bytes:
    """Build a PDF with one page per string (an empty string makes a blank page)."""
    pdf = FPDF()
    pdf.set_font("Helvetica", size=12)
    for text in pages:
        pdf.add_page()
        if text:
            pdf.multi_cell(0, 10, text)
    return bytes(pdf.output())


@pytest.fixture
def store(tmp_path: Path) -> VectorStore:
    return VectorStore(tmp_path / "chroma", fake_embed)


@pytest.fixture
def client(store: VectorStore) -> Iterator[TestClient]:
    """API client wired to the temporary store instead of the real one."""
    app.dependency_overrides[get_vector_store] = lambda: store
    yield TestClient(app)
    app.dependency_overrides.clear()

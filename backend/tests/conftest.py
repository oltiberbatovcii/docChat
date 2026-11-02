"""Shared test helpers: fake PDFs, a fake embedder, and a temporary vector store."""

import io
from collections.abc import Iterator
from pathlib import Path

import pytest
from docx import Document
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


def make_docx_bytes(blocks: list[tuple[str, str]]) -> bytes:
    """Build a Word file from (kind, text) pairs; kind is "heading", "paragraph" or "table".

    For "table", the text is rows separated by ";" and cells by ",".
    """
    document = Document()
    for kind, text in blocks:
        if kind == "heading":
            document.add_heading(text, level=1)
        elif kind == "paragraph":
            document.add_paragraph(text)
        else:
            rows = [row.split(",") for row in text.split(";")]
            table = document.add_table(rows=len(rows), cols=len(rows[0]))
            for row_cells, values in zip(table.rows, rows, strict=True):
                for cell, value in zip(row_cells.cells, values, strict=True):
                    cell.text = value
    buffer = io.BytesIO()
    document.save(buffer)
    return buffer.getvalue()


@pytest.fixture
def store(tmp_path: Path) -> VectorStore:
    return VectorStore(tmp_path / "chroma", fake_embed)


@pytest.fixture
def client(store: VectorStore) -> Iterator[TestClient]:
    """API client wired to the temporary store instead of the real one."""
    app.dependency_overrides[get_vector_store] = lambda: store
    yield TestClient(app)
    app.dependency_overrides.clear()

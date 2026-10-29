"""Ingestion pipeline: PDF bytes -> pages -> chunks -> vector store."""

import hashlib
import io

from app.services.chunking import chunk_pages
from app.services.pdf_loader import load_pdf
from app.services.vector_store import DocumentInfo, VectorStore


class NoTextError(ValueError):
    """The PDF has no extractable text (blank, or scanned images without OCR)."""


def ingest_pdf(
    data: bytes, filename: str, store: VectorStore, chunk_size: int, chunk_overlap: int
) -> DocumentInfo:
    # Content hash as ID: uploading the same file twice replaces it instead of duplicating it
    document_id = hashlib.sha256(data).hexdigest()[:16]

    pages = load_pdf(io.BytesIO(data))
    if not pages:
        raise NoTextError(f"{filename} has no extractable text")

    chunks = chunk_pages(pages, filename, chunk_size, chunk_overlap)
    store.add_chunks(document_id, chunks, pages=len(pages))
    return DocumentInfo(
        document_id=document_id, filename=filename, pages=len(pages), chunks=len(chunks)
    )

"""Ingestion pipeline: file bytes -> pages/sections -> chunks -> vector store."""

import hashlib

from app.services.chunking import chunk_pages
from app.services.loaders import FileFormat
from app.services.vector_store import DocumentInfo, VectorStore


class NoTextError(ValueError):
    """The document has no extractable text (empty, or scanned images without OCR)."""


def ingest_document(
    data: bytes,
    filename: str,
    file_format: FileFormat,
    store: VectorStore,
    chunk_size: int,
    chunk_overlap: int,
) -> DocumentInfo:
    # Content hash as ID: uploading the same file twice replaces it instead of duplicating it
    document_id = hashlib.sha256(data).hexdigest()[:16]

    pages = file_format.load(data)
    if not pages:
        raise NoTextError(f"{filename} has no extractable text")

    chunks = chunk_pages(pages, filename, chunk_size, chunk_overlap)
    store.add_chunks(document_id, chunks, pages=len(pages))
    return DocumentInfo(
        document_id=document_id, filename=filename, pages=len(pages), chunks=len(chunks)
    )

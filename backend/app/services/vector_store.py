"""ChromaDB wrapper: the only module that knows Chroma exists.

Keeping Chroma behind this small interface means it can later be swapped
(e.g. for Qdrant) without touching routes or other services.
"""

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import chromadb

from app.services.chunking import Chunk

# Injected instead of imported, so tests can pass a fast fake instead of a 90 MB model
EmbedFn = Callable[[list[str]], list[list[float]]]


@dataclass(frozen=True)
class SearchResult:
    text: str
    filename: str
    page: int
    chunk_index: int
    score: float  # cosine similarity: 1 = same meaning, 0 = unrelated


@dataclass(frozen=True)
class DocumentInfo:
    document_id: str
    filename: str
    pages: int
    chunks: int


class VectorStore:
    def __init__(self, persist_dir: Path, embed: EmbedFn, collection_name: str = "chunks") -> None:
        client = chromadb.PersistentClient(path=str(persist_dir))
        self._collection = client.get_or_create_collection(
            collection_name, configuration={"hnsw": {"space": "cosine"}}
        )
        self._embed = embed

    def add_chunks(self, document_id: str, chunks: list[Chunk], pages: int) -> None:
        """Store a document's chunks, replacing any earlier version of the same document."""
        # Delete first: a re-upload with a different chunk size could leave stale chunks behind
        self._collection.delete(where={"document_id": document_id})
        if not chunks:
            return

        texts = [chunk.text for chunk in chunks]
        self._collection.add(
            ids=[f"{document_id}:{chunk.chunk_index}" for chunk in chunks],
            documents=texts,
            embeddings=self._embed(texts),
            metadatas=[
                {
                    "document_id": document_id,
                    "filename": chunk.filename,
                    "page": chunk.page,
                    "chunk_index": chunk.chunk_index,
                    "pages": pages,
                }
                for chunk in chunks
            ],
        )

    def query(self, text: str, top_k: int) -> list[SearchResult]:
        """Return the `top_k` chunks closest in meaning to `text`, best first."""
        result = self._collection.query(
            query_embeddings=self._embed([text]),
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )
        # Chroma returns one list per query embedding; we always send exactly one
        return [
            SearchResult(
                text=document,
                filename=str(metadata["filename"]),
                page=int(metadata["page"]),
                chunk_index=int(metadata["chunk_index"]),
                score=1 - distance,  # Chroma reports cosine *distance*
            )
            for document, metadata, distance in zip(
                result["documents"][0], result["metadatas"][0], result["distances"][0], strict=True
            )
        ]

    def list_documents(self) -> list[DocumentInfo]:
        """Summarize stored documents by grouping chunk metadata per document."""
        documents: dict[str, DocumentInfo] = {}
        for metadata in self._collection.get(include=["metadatas"])["metadatas"]:
            document_id = str(metadata["document_id"])
            seen = documents.get(document_id)
            documents[document_id] = DocumentInfo(
                document_id=document_id,
                filename=str(metadata["filename"]),
                pages=int(metadata["pages"]),
                chunks=(seen.chunks if seen else 0) + 1,
            )
        return sorted(documents.values(), key=lambda doc: doc.filename)

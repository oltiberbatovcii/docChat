"""Split page text into overlapping chunks that keep their source metadata."""

from collections.abc import Iterable
from dataclasses import dataclass

from app.services.pdf_loader import PageText


@dataclass(frozen=True)
class Chunk:
    text: str
    filename: str
    page: int
    chunk_index: int  # position within the whole document, not within the page


def split_text(text: str, chunk_size: int, chunk_overlap: int) -> list[str]:
    """Split text into windows of `chunk_size` characters.

    Each window starts `chunk_size - chunk_overlap` characters after the previous one,
    so neighbouring chunks share `chunk_overlap` characters. That way a sentence cut
    at a boundary still appears whole in at least one chunk.
    """
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if not 0 <= chunk_overlap < chunk_size:
        raise ValueError("chunk_overlap must be >= 0 and smaller than chunk_size")

    step = chunk_size - chunk_overlap
    chunks = []
    for start in range(0, len(text), step):
        chunks.append(text[start : start + chunk_size])
        if start + chunk_size >= len(text):
            break  # this window already reached the end; another would only repeat the tail
    return chunks


def chunk_pages(
    pages: Iterable[PageText], filename: str, chunk_size: int, chunk_overlap: int
) -> list[Chunk]:
    """Chunk each page separately, so every chunk maps to exactly one page for citations."""
    chunks: list[Chunk] = []
    for page in pages:
        for text in split_text(page.text, chunk_size, chunk_overlap):
            chunks.append(
                Chunk(text=text, filename=filename, page=page.page, chunk_index=len(chunks))
            )
    return chunks

"""Types shared by every file-format loader."""

import re
from dataclasses import dataclass

_WHITESPACE = re.compile(r"\s+")


@dataclass(frozen=True)
class PageText:
    # 1-based. A real page number for PDFs; a section number for formats without pages
    page: int
    text: str


class UnreadableDocumentError(ValueError):
    """The file claims a supported format but can't be parsed (corrupt, encrypted, wrong type)."""


def clean_text(text: str) -> str:
    """Collapse runs of whitespace (documents are full of stray line breaks) into single spaces."""
    return _WHITESPACE.sub(" ", text).strip()


def numbered_parts(texts: list[str]) -> list[PageText]:
    """Clean each text, drop empty ones, and number the rest 1, 2, 3, ..."""
    cleaned = [clean_text(text) for text in texts]
    return [
        PageText(page=number, text=text) for number, text in enumerate(filter(None, cleaned), 1)
    ]

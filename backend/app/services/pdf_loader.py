"""Extract text from a PDF, one entry per page."""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO

from pypdf import PdfReader

_WHITESPACE = re.compile(r"\s+")


@dataclass(frozen=True)
class PageText:
    page: int  # 1-based, so it matches the page numbers people see in a PDF viewer
    text: str


def load_pdf(source: str | Path | BinaryIO) -> list[PageText]:
    """Return the cleaned text of every page that contains text.

    `source` can be a file path or an open binary stream (e.g. an uploaded file).
    Pages without extractable text (blank or scanned images) are skipped.
    """
    reader = PdfReader(source)
    pages = []
    for number, page in enumerate(reader.pages, start=1):
        text = clean_text(page.extract_text() or "")
        if text:
            pages.append(PageText(page=number, text=text))
    return pages


def clean_text(text: str) -> str:
    """Collapse runs of whitespace (PDFs are full of stray line breaks) into single spaces."""
    return _WHITESPACE.sub(" ", text).strip()

"""Registry of supported file formats: adding a format means adding one entry here."""

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from app.services.loaders.base import PageText, UnreadableDocumentError
from app.services.loaders.pdf_loader import load_pdf
from app.services.loaders.text_loader import load_markdown, load_text
from app.services.loaders.word_loader import load_docx


@dataclass(frozen=True)
class FileFormat:
    load: Callable[[bytes], list[PageText]]
    # Bytes the file must start with. The extension is only a name; this checks the content.
    # None for text formats, which have no signature (their loader rejects binary data instead).
    signature: bytes | None
    location_prefix: str  # how citations name a part: "p.3" or "section 3"


FORMATS = {
    ".pdf": FileFormat(load_pdf, b"%PDF-", "p."),
    ".docx": FileFormat(load_docx, b"PK\x03\x04", "section "),  # .docx files are zip archives
    ".md": FileFormat(load_markdown, None, "section "),
    ".txt": FileFormat(load_text, None, "section "),
}


def get_format(filename: str) -> FileFormat | None:
    return FORMATS.get(Path(filename).suffix.lower())


def location_label(filename: str, page: int) -> str:
    """Human-readable location for citations, e.g. "p.3" for a PDF or "section 3" for Word."""
    file_format = get_format(filename)
    prefix = file_format.location_prefix if file_format else "p."
    return f"{prefix}{page}"


__all__ = [
    "FORMATS",
    "FileFormat",
    "PageText",
    "UnreadableDocumentError",
    "get_format",
    "location_label",
]

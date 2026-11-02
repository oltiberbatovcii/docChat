"""Plain text and Markdown."""

import re

from app.services.loaders.base import PageText, UnreadableDocumentError, numbered_parts

_MARKDOWN_HEADING = re.compile(r"^#{1,6}\s")


def load_text(data: bytes) -> list[PageText]:
    """Plain text has no structure to split on: the whole file is one section."""
    return numbered_parts([_decode(data)])


def load_markdown(data: bytes) -> list[PageText]:
    """Start a new section at every heading line ("# Title", "## Subtitle", ...)."""
    sections: list[list[str]] = [[]]
    for line in _decode(data).splitlines():
        if _MARKDOWN_HEADING.match(line) and any(sections[-1]):
            sections.append([])
        sections[-1].append(line)
    return numbered_parts(["\n".join(section) for section in sections])


def _decode(data: bytes) -> str:
    try:
        text = data.decode("utf-8-sig")  # -sig: also accepts the BOM some Windows editors add
    except UnicodeDecodeError as error:
        raise UnreadableDocumentError("Text file is not valid UTF-8") from error
    # Valid UTF-8 can still be binary; NUL characters never occur in real text files
    if "\x00" in text:
        raise UnreadableDocumentError("File looks binary, not text")
    return text

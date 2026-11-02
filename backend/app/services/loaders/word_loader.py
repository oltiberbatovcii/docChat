"""Word (.docx): split into sections at headings, since .docx files have no fixed pages."""

import io
import zipfile

from docx import Document
from docx.opc.exceptions import PackageNotFoundError
from docx.table import Table
from docx.text.paragraph import Paragraph

from app.services.loaders.base import PageText, UnreadableDocumentError, numbered_parts

# A .docx is a zip file. A tiny "zip bomb" can unpack to gigabytes, so check before parsing.
MAX_UNCOMPRESSED_BYTES = 200 * 1024 * 1024


def load_docx(data: bytes, max_uncompressed_bytes: int = MAX_UNCOMPRESSED_BYTES) -> list[PageText]:
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            if sum(entry.file_size for entry in archive.infolist()) > max_uncompressed_bytes:
                raise UnreadableDocumentError("Word file unpacks to an unsafe size")
        document = Document(io.BytesIO(data))
    except (zipfile.BadZipFile, PackageNotFoundError, KeyError, ValueError) as error:
        if isinstance(error, UnreadableDocumentError):
            raise
        raise UnreadableDocumentError("Could not read Word file") from error

    sections: list[list[str]] = [[]]
    # iter_inner_content keeps paragraphs and tables in the order they appear in the document
    for block in document.iter_inner_content():
        if isinstance(block, Paragraph):
            if _is_heading(block) and any(sections[-1]):
                sections.append([])
            sections[-1].append(block.text)
        elif isinstance(block, Table):
            sections[-1].extend(_table_rows(block))
    return numbered_parts(["\n".join(section) for section in sections])


def _is_heading(paragraph: Paragraph) -> bool:
    style_name = paragraph.style.name if paragraph.style is not None else ""
    return style_name.startswith(("Heading", "Title"))


def _table_rows(table: Table) -> list[str]:
    """One line per row, cells separated by " | ", so the row's values stay together."""
    return [" | ".join(cell.text for cell in row.cells) for row in table.rows]

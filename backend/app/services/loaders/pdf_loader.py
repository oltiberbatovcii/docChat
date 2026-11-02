"""PDF: one part per page, numbered like a PDF viewer would show them."""

import io

from pypdf import PdfReader
from pypdf.errors import PdfReadError

from app.services.loaders.base import PageText, UnreadableDocumentError, clean_text


def load_pdf(data: bytes) -> list[PageText]:
    """Return the text of every page that has any.

    Blank or scanned (image-only) pages are skipped, but the remaining pages keep their real
    page numbers, so citations still match the PDF.
    """
    try:
        reader = PdfReader(io.BytesIO(data))
        pages = []
        for number, page in enumerate(reader.pages, start=1):
            text = clean_text(page.extract_text() or "")
            if text:
                pages.append(PageText(page=number, text=text))
    except PdfReadError as error:
        raise UnreadableDocumentError("Could not read PDF") from error
    return pages

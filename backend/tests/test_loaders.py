import io
import zipfile

import pytest

from app.services.loaders import FORMATS, UnreadableDocumentError, get_format, location_label
from app.services.loaders.base import clean_text
from app.services.loaders.pdf_loader import load_pdf
from app.services.loaders.text_loader import load_markdown, load_text
from app.services.loaders.word_loader import load_docx
from tests.conftest import make_docx_bytes, make_pdf_bytes

# --- PDF ---


def test_pdf_returns_text_per_page() -> None:
    pages = load_pdf(make_pdf_bytes(["First page", "Second page"]))

    assert [(p.page, p.text) for p in pages] == [(1, "First page"), (2, "Second page")]


def test_pdf_skips_blank_pages_but_keeps_real_page_numbers() -> None:
    pages = load_pdf(make_pdf_bytes(["Intro", "", "Ending"]))

    assert [p.page for p in pages] == [1, 3]


def test_corrupt_pdf_is_unreadable() -> None:
    with pytest.raises(UnreadableDocumentError):
        load_pdf(b"%PDF-1.4 garbage")


# --- Word ---


def test_docx_splits_into_sections_at_headings() -> None:
    data = make_docx_bytes(
        [
            ("paragraph", "Preface text"),
            ("heading", "Planets"),
            ("paragraph", "Mars is red"),
            ("heading", "Moons"),
            ("paragraph", "Ganymede is big"),
        ]
    )

    sections = load_docx(data)

    assert [(s.page, s.text) for s in sections] == [
        (1, "Preface text"),
        (2, "Planets Mars is red"),
        (3, "Moons Ganymede is big"),
    ]


def test_docx_keeps_table_rows_together_in_document_order() -> None:
    data = make_docx_bytes(
        [("paragraph", "Before"), ("table", "Planet,Moons;Mars,2"), ("paragraph", "After")]
    )

    [section] = load_docx(data)

    assert section.text == "Before Planet | Moons Mars | 2 After"


def test_zip_that_is_not_a_docx_is_unreadable() -> None:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("hello.txt", "not a Word document")

    with pytest.raises(UnreadableDocumentError):
        load_docx(buffer.getvalue())


def test_docx_that_unpacks_too_large_is_rejected() -> None:
    data = make_docx_bytes([("paragraph", "Hello")])

    with pytest.raises(UnreadableDocumentError, match="unsafe size"):
        load_docx(data, max_uncompressed_bytes=100)


# --- Text and Markdown ---


def test_text_file_is_one_section() -> None:
    sections = load_text(b"Line one\n\nLine two")

    assert [(s.page, s.text) for s in sections] == [(1, "Line one Line two")]


def test_markdown_splits_at_headings() -> None:
    data = b"Intro\n# Mars\nRed planet\n## Moons\nPhobos\n#hashtag is not a heading"

    sections = load_markdown(data)

    assert [s.text for s in sections] == [
        "Intro",
        "# Mars Red planet",
        "## Moons Phobos #hashtag is not a heading",
    ]


def test_text_with_byte_order_mark_is_accepted() -> None:
    assert load_text("﻿Hello".encode())[0].text == "Hello"


@pytest.mark.parametrize("data", [b"\xff\xfe\x00bad", b"MZ\x00\x00binary"])
def test_non_text_bytes_are_unreadable(data: bytes) -> None:
    with pytest.raises(UnreadableDocumentError):
        load_text(data)


# --- Registry ---


@pytest.mark.parametrize("filename", ["a.pdf", "a.PDF", "a.docx", "a.md", "a.txt"])
def test_supported_formats_are_found_case_insensitively(filename: str) -> None:
    assert get_format(filename) is not None


@pytest.mark.parametrize("filename", ["a.doc", "a.exe", "a", "a.pdf.exe"])
def test_unsupported_formats_are_not_found(filename: str) -> None:
    assert get_format(filename) is None


def test_location_label_depends_on_format() -> None:
    assert location_label("a.pdf", 3) == "p.3"
    assert location_label("a.docx", 3) == "section 3"
    assert set(FORMATS) == {".pdf", ".docx", ".md", ".txt"}


def test_clean_text_collapses_whitespace() -> None:
    assert clean_text("  Hello\n\n  world\t! ") == "Hello world !"

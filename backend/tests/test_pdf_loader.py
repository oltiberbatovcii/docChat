import io
from pathlib import Path

from app.services.pdf_loader import clean_text, load_pdf
from tests.conftest import make_pdf_bytes


def test_load_pdf_returns_text_per_page() -> None:
    pages = load_pdf(io.BytesIO(make_pdf_bytes(["First page", "Second page"])))

    assert [(p.page, p.text) for p in pages] == [(1, "First page"), (2, "Second page")]


def test_load_pdf_skips_blank_pages_but_keeps_real_page_numbers() -> None:
    pages = load_pdf(io.BytesIO(make_pdf_bytes(["Intro", "", "Ending"])))

    assert [p.page for p in pages] == [1, 3]


def test_load_pdf_accepts_a_file_path(tmp_path: Path) -> None:
    pdf_path = tmp_path / "doc.pdf"
    pdf_path.write_bytes(make_pdf_bytes(["From disk"]))

    assert load_pdf(pdf_path)[0].text == "From disk"


def test_clean_text_collapses_whitespace() -> None:
    assert clean_text("  Hello\n\n  world\t! ") == "Hello world !"

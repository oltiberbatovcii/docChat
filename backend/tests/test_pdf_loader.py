from pathlib import Path

from fpdf import FPDF

from app.services.pdf_loader import clean_text, load_pdf


def make_pdf(path: Path, pages: list[str]) -> Path:
    """Write a PDF with one page per string (an empty string makes a blank page)."""
    pdf = FPDF()
    pdf.set_font("Helvetica", size=12)
    for text in pages:
        pdf.add_page()
        if text:
            pdf.multi_cell(0, 10, text)
    pdf.output(str(path))
    return path


def test_load_pdf_returns_text_per_page(tmp_path: Path) -> None:
    pdf_path = make_pdf(tmp_path / "doc.pdf", ["First page", "Second page"])

    pages = load_pdf(pdf_path)

    assert [(p.page, p.text) for p in pages] == [(1, "First page"), (2, "Second page")]


def test_load_pdf_skips_blank_pages_but_keeps_real_page_numbers(tmp_path: Path) -> None:
    pdf_path = make_pdf(tmp_path / "doc.pdf", ["Intro", "", "Ending"])

    pages = load_pdf(pdf_path)

    assert [p.page for p in pages] == [1, 3]


def test_load_pdf_accepts_a_binary_stream(tmp_path: Path) -> None:
    pdf_path = make_pdf(tmp_path / "doc.pdf", ["Streamed"])

    with pdf_path.open("rb") as stream:
        pages = load_pdf(stream)

    assert pages[0].text == "Streamed"


def test_clean_text_collapses_whitespace() -> None:
    assert clean_text("  Hello\n\n  world\t! ") == "Hello world !"

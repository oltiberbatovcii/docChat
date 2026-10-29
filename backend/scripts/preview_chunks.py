"""Print how a PDF gets chunked. Usage: uv run python -m scripts.preview_chunks <file.pdf>"""

import argparse
from pathlib import Path

from app.core.config import get_settings
from app.services.chunking import chunk_pages
from app.services.pdf_loader import load_pdf


def main() -> None:
    settings = get_settings()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--chunk-size", type=int, default=settings.chunk_size)
    parser.add_argument("--chunk-overlap", type=int, default=settings.chunk_overlap)
    args = parser.parse_args()
    if not args.pdf.is_file():
        parser.error(f"file not found: {args.pdf}")

    pages = load_pdf(args.pdf)
    chunks = chunk_pages(pages, args.pdf.name, args.chunk_size, args.chunk_overlap)

    print(f"{args.pdf.name}: {len(pages)} pages with text -> {len(chunks)} chunks\n")
    for chunk in chunks[:5]:
        print(f"[#{chunk.chunk_index} p.{chunk.page}] {chunk.text[:120]}...")


if __name__ == "__main__":
    main()

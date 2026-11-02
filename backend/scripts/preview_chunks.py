"""Print how a document gets chunked. Usage: uv run python -m scripts.preview_chunks <file>"""

import argparse
from pathlib import Path

from app.core.config import get_settings
from app.services.chunking import chunk_pages
from app.services.loaders import FORMATS, get_format, location_label


def main() -> None:
    settings = get_settings()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", type=Path)
    parser.add_argument("--chunk-size", type=int, default=settings.chunk_size)
    parser.add_argument("--chunk-overlap", type=int, default=settings.chunk_overlap)
    args = parser.parse_args()
    if not args.file.is_file():
        parser.error(f"file not found: {args.file}")
    file_format = get_format(args.file.name)
    if file_format is None:
        parser.error(f"unsupported format; supported: {', '.join(FORMATS)}")

    pages = file_format.load(args.file.read_bytes())
    chunks = chunk_pages(pages, args.file.name, args.chunk_size, args.chunk_overlap)

    print(f"{args.file.name}: {len(pages)} parts with text -> {len(chunks)} chunks\n")
    for chunk in chunks[:5]:
        location = location_label(chunk.filename, chunk.page)
        print(f"[#{chunk.chunk_index} {location}] {chunk.text[:120]}...")


if __name__ == "__main__":
    main()

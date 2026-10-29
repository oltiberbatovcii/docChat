import pytest

from app.services.chunking import chunk_pages, split_text
from app.services.pdf_loader import PageText


def test_empty_text_gives_no_chunks() -> None:
    assert split_text("", chunk_size=10, chunk_overlap=2) == []


def test_text_shorter_than_chunk_is_one_chunk() -> None:
    assert split_text("hello", chunk_size=10, chunk_overlap=2) == ["hello"]


def test_text_exactly_chunk_size_is_one_chunk() -> None:
    assert split_text("abcdefghij", chunk_size=10, chunk_overlap=2) == ["abcdefghij"]


def test_neighbouring_chunks_share_the_overlap() -> None:
    chunks = split_text("abcdefghijklmnopqrstuvwxyz", chunk_size=10, chunk_overlap=3)

    assert chunks == ["abcdefghij", "hijklmnopq", "opqrstuvwx", "vwxyz"]
    for previous, current in zip(chunks, chunks[1:], strict=False):
        assert previous[-3:] == current[:3]


def test_zero_overlap_splits_cleanly() -> None:
    assert split_text("abcdef", chunk_size=2, chunk_overlap=0) == ["ab", "cd", "ef"]


@pytest.mark.parametrize(
    ("chunk_size", "chunk_overlap"),
    [(0, 0), (-5, 0), (10, 10), (10, 15), (10, -1)],
)
def test_invalid_settings_raise(chunk_size: int, chunk_overlap: int) -> None:
    with pytest.raises(ValueError):
        split_text("some text", chunk_size=chunk_size, chunk_overlap=chunk_overlap)


def test_chunk_pages_keeps_metadata_and_numbers_chunks_across_pages() -> None:
    pages = [PageText(page=1, text="a" * 15), PageText(page=3, text="b" * 5)]

    chunks = chunk_pages(pages, filename="doc.pdf", chunk_size=10, chunk_overlap=0)

    assert [(c.page, c.chunk_index) for c in chunks] == [(1, 0), (1, 1), (3, 2)]
    assert all(c.filename == "doc.pdf" for c in chunks)

from app.services.chunking import Chunk
from app.services.vector_store import VectorStore


def make_chunks(filename: str, texts: list[str]) -> list[Chunk]:
    return [
        Chunk(text=text, filename=filename, page=index + 1, chunk_index=index)
        for index, text in enumerate(texts)
    ]


def test_query_returns_most_similar_chunk_first(store: VectorStore) -> None:
    chunks = make_chunks("space.pdf", ["Venus is hot", "Jupiter is big", "Mars is red"])
    store.add_chunks("doc1", chunks, pages=3)

    results = store.query("Tell me about Jupiter", top_k=2)

    assert len(results) == 2
    assert results[0].text == "Jupiter is big"
    assert (results[0].filename, results[0].page) == ("space.pdf", 2)
    assert results[0].score > results[1].score


def test_re_adding_a_document_replaces_its_old_chunks(store: VectorStore) -> None:
    store.add_chunks("doc1", make_chunks("a.pdf", ["one", "two", "three"]), pages=3)
    store.add_chunks("doc1", make_chunks("a.pdf", ["only one now"]), pages=1)

    [document] = store.list_documents()
    assert (document.chunks, document.pages) == (1, 1)


def test_list_documents_groups_chunks_per_document(store: VectorStore) -> None:
    store.add_chunks("doc1", make_chunks("b.pdf", ["x", "y"]), pages=2)
    store.add_chunks("doc2", make_chunks("a.pdf", ["z"]), pages=1)

    summary = [(d.document_id, d.filename, d.chunks) for d in store.list_documents()]

    assert summary == [("doc2", "a.pdf", 1), ("doc1", "b.pdf", 2)]  # sorted by filename


def test_empty_store_lists_nothing(store: VectorStore) -> None:
    assert store.list_documents() == []

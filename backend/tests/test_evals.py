import pytest

from app.services.chunking import Chunk
from app.services.vector_store import SearchResult, VectorStore
from evals.run_evals import (
    EVALS_DIR,
    EvalItem,
    ExpectedSource,
    evaluate_item,
    load_dataset,
    parse_judge_score,
    reciprocal_rank,
    summarize,
)


def result_on_page(page: int) -> SearchResult:
    return SearchResult(text="x", filename="a.pdf", page=page, chunk_index=0, score=0.5)


@pytest.mark.parametrize(
    ("pages", "expected_rank"),
    [([2, 1], 1.0), ([1, 2], 0.5), ([1, 3, 2], 1 / 3), ([1, 3], 0.0), ([], 0.0)],
)
def test_reciprocal_rank(pages: list[int], expected_rank: float) -> None:
    results = [result_on_page(page) for page in pages]

    assert reciprocal_rank(results, ExpectedSource(filename="a.pdf", page=2)) == expected_rank


@pytest.mark.parametrize(
    ("reply", "score"),
    [("4", 4), ("Score: 5", 5), ("I'd say 2 out of 5", 2), ("no number", None), ("9", None)],
)
def test_parse_judge_score(reply: str, score: int | None) -> None:
    assert parse_judge_score(reply) == score


def fake_llm(answer: str):
    """Plays both roles: the judge (recognised by its prompt) and the answering model."""

    def generate(system: str, user: str) -> str:
        return "4" if "grade" in system else answer

    return generate


@pytest.fixture
def store_with_venus(store: VectorStore) -> VectorStore:
    chunk = Chunk(text="Venus is hot", filename="a.pdf", page=1, chunk_index=0)
    store.add_chunks("doc", [chunk], pages=1)
    return store


ANSWERABLE = EvalItem(
    question="Tell me about Venus",
    expected_answer="It is hot",
    expected_source=ExpectedSource(filename="a.pdf", page=1),
)
UNANSWERABLE = EvalItem(question="Capital of France?", expected_answer=None, expected_source=None)


def test_correct_answer_with_citation_scores_well(store_with_venus: VectorStore) -> None:
    llm = fake_llm("Venus is hot [a.pdf p.1]")

    result = evaluate_item(ANSWERABLE, store_with_venus, llm, top_k=1)

    assert (result.reciprocal_rank, result.judge_score, result.cited_correctly) == (1.0, 4, True)


def test_refusing_an_answerable_question_scores_lowest(store_with_venus: VectorStore) -> None:
    result = evaluate_item(ANSWERABLE, store_with_venus, fake_llm("I don't know."), top_k=1)

    assert result.refused
    assert result.judge_score == 1


def test_unanswerable_question_only_tracks_refusal(store_with_venus: VectorStore) -> None:
    result = evaluate_item(UNANSWERABLE, store_with_venus, fake_llm("I don't know."), top_k=1)

    assert result.refused
    assert (result.reciprocal_rank, result.judge_score, result.cited_correctly) == (None,) * 3


def test_summarize_separates_answerable_and_unanswerable(store_with_venus: VectorStore) -> None:
    results = [
        evaluate_item(ANSWERABLE, store_with_venus, fake_llm("Hot [a.pdf p.1]"), top_k=1),
        evaluate_item(ANSWERABLE, store_with_venus, fake_llm("I don't know."), top_k=1),
        evaluate_item(UNANSWERABLE, store_with_venus, fake_llm("Paris"), top_k=1),
    ]

    summary = summarize(results)

    assert summary["hit_rate_at_k"] == 1.0
    assert summary["answer_correctness_1_to_5"] == 2.5  # judged 4, plus 1 for the refusal
    assert summary["citation_accuracy"] == 0.5
    assert summary["false_refusal_rate"] == 0.5
    assert summary["refusal_accuracy"] == 0.0


def test_dataset_is_valid_and_includes_unanswerable_questions() -> None:
    dataset = load_dataset(EVALS_DIR / "dataset.jsonl")

    unanswerable = [item for item in dataset if item.expected_source is None]
    assert 15 <= len(dataset) <= 25
    assert len(unanswerable) >= 3
    assert all((item.expected_answer is None) == (item.expected_source is None) for item in dataset)

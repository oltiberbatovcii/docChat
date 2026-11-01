"""Measure RAG quality. Usage: uv run python -m evals.run_evals --label baseline"""

import argparse
import json
import re
import tempfile
from dataclasses import asdict, dataclass
from datetime import datetime
from functools import partial
from pathlib import Path

from pydantic import BaseModel

from app.api.deps import get_generate
from app.core.config import get_settings
from app.prompts.answer_prompts import REFUSAL
from app.services.embeddings import embed_texts
from app.services.ingestion import ingest_pdf
from app.services.rag import GenerateFn, answer_question
from app.services.vector_store import SearchResult, VectorStore

EVALS_DIR = Path(__file__).parent
PDFS_DIR = EVALS_DIR / "pdfs"
RESULTS_DIR = EVALS_DIR / "results"

JUDGE_SYSTEM = (
    "You grade answers against an expected answer. Score from 1 to 5:\n"
    "5 = fully correct, 3 = partly correct, 1 = wrong or unrelated.\n"
    "Ignore style and citations such as [file.pdf p.1]. Reply with the number only."
)
JUDGE_USER = "Question: {question}\nExpected answer: {expected}\nActual answer: {actual}"


class ExpectedSource(BaseModel):
    filename: str
    page: int


class EvalItem(BaseModel):
    question: str
    # Both None means the documents can't answer it, so the correct behaviour is a refusal
    expected_answer: str | None
    expected_source: ExpectedSource | None


@dataclass(frozen=True)
class ItemResult:
    question: str
    answerable: bool
    answer: str
    refused: bool
    retrieved_pages: list[int]
    # The fields below only apply to answerable questions
    reciprocal_rank: float | None
    judge_score: int | None
    cited_correctly: bool | None


def load_dataset(path: Path) -> list[EvalItem]:
    lines = path.read_text(encoding="utf-8").splitlines()
    return [EvalItem.model_validate_json(line) for line in lines if line.strip()]


def reciprocal_rank(results: list[SearchResult], expected: ExpectedSource) -> float:
    """1 / position of the first chunk from the expected page; 0 if it wasn't retrieved."""
    for position, result in enumerate(results, start=1):
        if (result.filename, result.page) == (expected.filename, expected.page):
            return 1 / position
    return 0.0


def parse_judge_score(reply: str) -> int | None:
    """Pull the score out of the reply: models sometimes add words around the number."""
    match = re.search(r"[1-5]", reply)
    return int(match.group()) if match else None


def judge_answer(question: str, expected: str, answer: str, generate: GenerateFn) -> int | None:
    user = JUDGE_USER.format(question=question, expected=expected, actual=answer)
    return parse_judge_score(generate(JUDGE_SYSTEM, user))


def evaluate_item(
    item: EvalItem, store: VectorStore, generate: GenerateFn, top_k: int
) -> ItemResult:
    results = store.query(item.question, top_k)
    answer = answer_question(item.question, top_k, store, generate).answer
    refused = answer.startswith(REFUSAL)
    retrieved_pages = [result.page for result in results]

    if item.expected_source is None or item.expected_answer is None:
        return ItemResult(item.question, False, answer, refused, retrieved_pages, None, None, None)

    citation = f"[{item.expected_source.filename} p.{item.expected_source.page}]"
    # A refusal of an answerable question is simply wrong, so don't spend a judge call on it
    score = 1 if refused else judge_answer(item.question, item.expected_answer, answer, generate)
    return ItemResult(
        question=item.question,
        answerable=True,
        answer=answer,
        refused=refused,
        retrieved_pages=retrieved_pages,
        reciprocal_rank=reciprocal_rank(results, item.expected_source),
        judge_score=score,
        cited_correctly=citation in answer,
    )


def mean(values: list[float]) -> float | None:
    return round(sum(values) / len(values), 3) if values else None


def summarize(results: list[ItemResult]) -> dict[str, float | int | None]:
    answerable = [r for r in results if r.answerable]
    unanswerable = [r for r in results if not r.answerable]
    ranks = [r.reciprocal_rank for r in answerable if r.reciprocal_rank is not None]
    scores = [r.judge_score for r in answerable if r.judge_score is not None]
    return {
        "hit_rate_at_k": mean([float(rank > 0) for rank in ranks]),
        "hit_rate_at_1": mean([float(rank == 1) for rank in ranks]),
        "mrr": mean(ranks),
        "answer_correctness_1_to_5": mean(scores),
        "unjudged_answers": len(answerable) - len(scores),
        "citation_accuracy": mean([float(bool(r.cited_correctly)) for r in answerable]),
        "refusal_accuracy": mean([float(r.refused) for r in unanswerable]),
        "false_refusal_rate": mean([float(r.refused) for r in answerable]),
    }


def build_store(persist_dir: Path, chunk_size: int, chunk_overlap: int) -> VectorStore:
    """Index the eval documents into a throwaway store, separate from real uploads."""
    embed = partial(embed_texts, model_name=get_settings().embedding_model)
    store = VectorStore(persist_dir, embed)
    for pdf in sorted(PDFS_DIR.glob("*.pdf")):
        ingest_pdf(pdf.read_bytes(), pdf.name, store, chunk_size, chunk_overlap)
    return store


def print_report(results: list[ItemResult], summary: dict[str, float | int | None]) -> None:
    print(f"\n{'rank':>5} {'judge':>5} {'cited':>5} {'refused':>7}  question")
    for r in results:
        rank = "-" if r.reciprocal_rank is None else f"{r.reciprocal_rank:.2f}"
        judge = "-" if r.judge_score is None else r.judge_score
        cited = "-" if r.cited_correctly is None else ("yes" if r.cited_correctly else "no")
        print(f"{rank:>5} {judge!s:>5} {cited:>5} {'yes' if r.refused else 'no':>7}  {r.question}")
    print("\nSummary")
    for name, value in summary.items():
        print(f"  {name:<28} {value}")


def main() -> None:
    settings = get_settings()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--label", required=True, help="name for this run, e.g. baseline")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--chunk-size", type=int, default=settings.chunk_size)
    parser.add_argument("--chunk-overlap", type=int, default=settings.chunk_overlap)
    args = parser.parse_args()
    # The label becomes part of a filename
    if not re.fullmatch(r"[\w-]+", args.label):
        parser.error("--label may only contain letters, digits, _ and -")

    dataset = load_dataset(EVALS_DIR / "dataset.jsonl")
    generate = get_generate(settings)
    # ignore_cleanup_errors: on Windows, Chroma can still hold its files open at exit
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
        store = build_store(Path(temp_dir), args.chunk_size, args.chunk_overlap)
        results = []
        for number, item in enumerate(dataset, start=1):
            print(f"[{number}/{len(dataset)}] {item.question}", flush=True)
            results.append(evaluate_item(item, store, generate, args.top_k))

    summary = summarize(results)
    print_report(results, summary)

    RESULTS_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output = RESULTS_DIR / f"{timestamp}_{args.label}.json"
    config = {
        "model": settings.ollama_model,
        "top_k": args.top_k,
        "chunk_size": args.chunk_size,
        "chunk_overlap": args.chunk_overlap,
    }
    run = {"config": config, "summary": summary, "items": [asdict(r) for r in results]}
    output.write_text(json.dumps(run, indent=2), encoding="utf-8")
    print(f"\nSaved {output}")


if __name__ == "__main__":
    main()

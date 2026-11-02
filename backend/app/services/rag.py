"""RAG pipeline: retrieve relevant chunks -> build a prompt -> generate an answer."""

from collections.abc import Callable
from dataclasses import dataclass

from app.prompts.answer_prompts import PROMPT_V1, REFUSAL, PromptTemplate
from app.services.loaders import location_label
from app.services.vector_store import SearchResult, VectorStore

GenerateFn = Callable[[str, str], str]  # (system prompt, user prompt) -> reply

SNIPPET_LENGTH = 200


@dataclass(frozen=True)
class Source:
    filename: str
    page: int
    location: str
    snippet: str


@dataclass(frozen=True)
class RagAnswer:
    answer: str
    sources: list[Source]


def build_context(results: list[SearchResult]) -> str:
    """Label each chunk with its citation, so the LLM can copy the label into its answer."""
    return "\n\n".join(f"[{citation(r)}]\n{r.text}" for r in results)


def citation(result: SearchResult) -> str:
    return f"{result.filename} {location_label(result.filename, result.page)}"


def answer_question(
    question: str,
    top_k: int,
    store: VectorStore,
    generate: GenerateFn,
    prompt: PromptTemplate = PROMPT_V1,
) -> RagAnswer:
    results = store.query(question, top_k)
    if not results:
        # Nothing uploaded yet: skip the LLM, since it could only guess
        return RagAnswer(answer=f"{REFUSAL}.", sources=[])

    user_prompt = prompt.user.format(context=build_context(results), question=question)
    answer = generate(prompt.system, user_prompt)

    # A refusal didn't use the retrieved chunks, so citing them would be misleading
    if answer.startswith(REFUSAL):
        return RagAnswer(answer=answer, sources=[])
    sources = [
        Source(r.filename, r.page, location_label(r.filename, r.page), r.text[:SNIPPET_LENGTH])
        for r in results
    ]
    return RagAnswer(answer=answer, sources=sources)

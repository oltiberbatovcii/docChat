from collections.abc import Callable

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_generate
from app.main import app
from app.services.llm import LLMError
from tests.conftest import make_pdf_bytes


class FakeLLM:
    """Stands in for Ollama: returns a fixed reply and records the prompts it received."""

    def __init__(self, reply: str = "Venus is the hottest [space.pdf p.1]") -> None:
        self.reply = reply
        self.calls: list[tuple[str, str]] = []

    def __call__(self, system: str, user: str) -> str:
        self.calls.append((system, user))
        return self.reply


@pytest.fixture
def use_llm(client: TestClient) -> Callable[[Callable[[str, str], str]], None]:
    """Returns a function that swaps the given fake in place of the real LLM."""

    def install(fake: Callable[[str, str], str]) -> None:
        app.dependency_overrides[get_generate] = lambda: fake

    return install


def upload_sample(client: TestClient) -> None:
    pdf = make_pdf_bytes(["Venus is hot", "Jupiter is big"])
    client.post("/documents", files={"file": ("space.pdf", pdf, "application/pdf")})


def test_chat_returns_answer_with_sources(client: TestClient, use_llm) -> None:
    use_llm(FakeLLM())
    upload_sample(client)

    response = client.post("/chat", json={"question": "What about Venus?", "top_k": 1})

    assert response.status_code == 200
    assert response.json() == {
        "answer": "Venus is the hottest [space.pdf p.1]",
        "sources": [{"filename": "space.pdf", "page": 1, "snippet": "Venus is hot"}],
    }


def test_prompt_contains_labelled_context_and_question(client: TestClient, use_llm) -> None:
    fake = FakeLLM()
    use_llm(fake)
    upload_sample(client)

    client.post("/chat", json={"question": "What about Venus?", "top_k": 1})

    system, user = fake.calls[0]
    assert "only" in system
    assert "[space.pdf p.1]\nVenus is hot" in user
    assert "Question: What about Venus?" in user


def test_refusal_has_no_sources(client: TestClient, use_llm) -> None:
    use_llm(FakeLLM(reply="I don't know."))
    upload_sample(client)

    response = client.post("/chat", json={"question": "Capital of France?"})

    assert response.json() == {"answer": "I don't know.", "sources": []}


def test_empty_store_refuses_without_calling_the_llm(client: TestClient, use_llm) -> None:
    fake = FakeLLM()
    use_llm(fake)

    response = client.post("/chat", json={"question": "Anything?"})

    assert response.json()["answer"] == "I don't know."
    assert fake.calls == []


def test_llm_failure_returns_503(client: TestClient, use_llm) -> None:
    def failing_llm(system: str, user: str) -> str:
        raise LLMError("connection refused")

    use_llm(failing_llm)
    upload_sample(client)

    response = client.post("/chat", json={"question": "What about Venus?"})

    assert response.status_code == 503


@pytest.mark.parametrize(
    "body", [{"question": "   "}, {"question": "ok", "top_k": 11}, {"top_k": 3}]
)
def test_invalid_requests_are_rejected(client: TestClient, body: dict) -> None:
    assert client.post("/chat", json=body).status_code == 422

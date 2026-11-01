import pytest
from fastapi.testclient import TestClient

from tests.conftest import make_pdf_bytes


@pytest.fixture
def client_with_document(client: TestClient) -> TestClient:
    pdf = make_pdf_bytes(["Venus is hot", "Jupiter is big", "Mars is red"])
    client.post("/documents", files={"file": ("space.pdf", pdf, "application/pdf")})
    return client


def test_search_returns_best_match_first_with_citation(client_with_document: TestClient) -> None:
    response = client_with_document.post("/search", json={"query": "about Jupiter", "top_k": 2})

    assert response.status_code == 200
    results = response.json()
    assert len(results) == 2
    assert results[0]["text"] == "Jupiter is big"
    assert (results[0]["filename"], results[0]["page"]) == ("space.pdf", 2)
    assert results[0]["score"] > results[1]["score"]


def test_top_k_larger_than_stored_chunks_returns_what_exists(
    client_with_document: TestClient,
) -> None:
    response = client_with_document.post("/search", json={"query": "Mars", "top_k": 20})

    assert response.status_code == 200
    assert len(response.json()) == 3


def test_search_on_empty_store_returns_empty_list(client: TestClient) -> None:
    response = client.post("/search", json={"query": "anything"})

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.parametrize(
    "body",
    [
        {"query": ""},
        {"query": "   "},
        {"query": "x" * 1001},
        {"query": "ok", "top_k": 0},
        {"query": "ok", "top_k": 21},
        {"top_k": 5},
    ],
)
def test_invalid_requests_are_rejected(client: TestClient, body: dict) -> None:
    assert client.post("/search", json=body).status_code == 422

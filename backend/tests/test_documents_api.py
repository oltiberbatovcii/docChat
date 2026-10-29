from fastapi.testclient import TestClient

from app.core.config import Settings, get_settings
from app.main import app
from tests.conftest import make_pdf_bytes


def upload(client: TestClient, filename: str, data: bytes):
    return client.post("/documents", files={"file": (filename, data, "application/pdf")})


def test_upload_pdf_returns_document_summary(client: TestClient) -> None:
    response = upload(client, "space.pdf", make_pdf_bytes(["Venus is hot", "Mars is red"]))

    assert response.status_code == 201
    body = response.json()
    assert (body["filename"], body["pages"], body["chunks"]) == ("space.pdf", 2, 2)


def test_uploaded_document_appears_in_list(client: TestClient) -> None:
    upload(client, "space.pdf", make_pdf_bytes(["Venus is hot"]))

    response = client.get("/documents")

    assert response.status_code == 200
    assert [doc["filename"] for doc in response.json()] == ["space.pdf"]


def test_uploading_same_file_twice_does_not_duplicate_it(client: TestClient) -> None:
    data = make_pdf_bytes(["Venus is hot"])
    first = upload(client, "space.pdf", data).json()
    second = upload(client, "space.pdf", data).json()

    assert first["document_id"] == second["document_id"]
    assert len(client.get("/documents").json()) == 1


def test_client_supplied_path_is_stripped_from_filename(client: TestClient) -> None:
    response = upload(client, "../../secret/space.pdf", make_pdf_bytes(["Venus"]))

    assert response.json()["filename"] == "space.pdf"


def test_non_pdf_extension_is_rejected(client: TestClient) -> None:
    assert upload(client, "notes.txt", b"hello").status_code == 415


def test_fake_pdf_with_wrong_content_is_rejected(client: TestClient) -> None:
    assert upload(client, "evil.pdf", b"MZ this is really an exe").status_code == 415


def test_corrupt_pdf_is_rejected(client: TestClient) -> None:
    assert upload(client, "broken.pdf", b"%PDF-1.4 garbage").status_code == 422


def test_pdf_without_text_is_rejected(client: TestClient) -> None:
    assert upload(client, "blank.pdf", make_pdf_bytes([""])).status_code == 422


def test_file_over_size_limit_is_rejected(client: TestClient) -> None:
    app.dependency_overrides[get_settings] = lambda: Settings(max_upload_mb=1)
    too_big = b"%PDF-" + b"0" * (1024 * 1024)

    assert upload(client, "big.pdf", too_big).status_code == 413

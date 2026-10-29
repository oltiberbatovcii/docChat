"""Upload PDFs and list what has been uploaded."""

from dataclasses import asdict
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, status
from pypdf.errors import PdfReadError

from app.api.deps import SettingsDep, VectorStoreDep
from app.schemas.documents import DocumentOut
from app.services.ingestion import NoTextError, ingest_pdf

router = APIRouter(prefix="/documents", tags=["documents"])

PDF_MAGIC = b"%PDF-"


# A plain `def` (not `async def`): parsing and embedding are CPU-heavy, so FastAPI
# runs this in a worker thread and the server stays responsive meanwhile.
@router.post("", status_code=status.HTTP_201_CREATED)
def upload_document(file: UploadFile, store: VectorStoreDep, settings: SettingsDep) -> DocumentOut:
    # Keep only the base name: never trust client paths like "../../etc/passwd.pdf"
    filename = Path(file.filename or "").name
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "Only .pdf files are accepted")

    max_bytes = settings.max_upload_mb * 1024 * 1024
    data = file.file.read(max_bytes + 1)  # read at most one byte past the limit
    if len(data) > max_bytes:
        raise HTTPException(
            status.HTTP_413_CONTENT_TOO_LARGE, f"File exceeds {settings.max_upload_mb} MB"
        )
    # The extension is just a name; the first bytes tell us if it really is a PDF
    if not data.startswith(PDF_MAGIC):
        raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "File is not a valid PDF")

    try:
        document = ingest_pdf(data, filename, store, settings.chunk_size, settings.chunk_overlap)
    except PdfReadError as error:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Could not read PDF") from error
    except NoTextError as error:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(error)) from error
    return DocumentOut(**asdict(document))


@router.get("")
def list_documents(store: VectorStoreDep) -> list[DocumentOut]:
    return [DocumentOut(**asdict(document)) for document in store.list_documents()]

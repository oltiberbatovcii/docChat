"""Upload documents and list what has been uploaded."""

from dataclasses import asdict
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, status

from app.api.deps import SettingsDep, VectorStoreDep
from app.schemas.documents import DocumentOut
from app.services.ingestion import NoTextError, ingest_document
from app.services.loaders import FORMATS, UnreadableDocumentError, get_format

router = APIRouter(prefix="/documents", tags=["documents"])

SUPPORTED = ", ".join(FORMATS)


# A plain `def` (not `async def`): parsing and embedding are CPU-heavy, so FastAPI
# runs this in a worker thread and the server stays responsive meanwhile.
@router.post("", status_code=status.HTTP_201_CREATED)
def upload_document(file: UploadFile, store: VectorStoreDep, settings: SettingsDep) -> DocumentOut:
    # Keep only the base name: never trust client paths like "../../etc/passwd.pdf"
    filename = Path(file.filename or "").name
    file_format = get_format(filename)
    if file_format is None:
        raise HTTPException(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, f"Supported formats: {SUPPORTED}"
        )

    max_bytes = settings.max_upload_mb * 1024 * 1024
    data = file.file.read(max_bytes + 1)  # read at most one byte past the limit
    if len(data) > max_bytes:
        raise HTTPException(
            status.HTTP_413_CONTENT_TOO_LARGE, f"File exceeds {settings.max_upload_mb} MB"
        )
    # The extension is just a name; the first bytes show what the file really is
    if file_format.signature and not data.startswith(file_format.signature):
        raise HTTPException(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "File content doesn't match its extension"
        )

    try:
        document = ingest_document(
            data, filename, file_format, store, settings.chunk_size, settings.chunk_overlap
        )
    except (UnreadableDocumentError, NoTextError) as error:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(error)) from error
    return DocumentOut(**asdict(document))


@router.get("")
def list_documents(store: VectorStoreDep) -> list[DocumentOut]:
    return [DocumentOut(**asdict(document)) for document in store.list_documents()]

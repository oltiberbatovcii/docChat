from pydantic import BaseModel


class DocumentOut(BaseModel):
    document_id: str
    filename: str
    pages: int
    chunks: int

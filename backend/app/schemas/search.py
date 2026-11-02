from pydantic import BaseModel, ConfigDict, Field


class SearchRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)  # so "   " counts as empty

    # Limits protect the server: a huge query or top_k would waste CPU and memory
    query: str = Field(min_length=1, max_length=1000)
    top_k: int = Field(default=5, ge=1, le=20)


class SearchResultOut(BaseModel):
    text: str
    filename: str
    page: int
    location: str  # citation-ready, e.g. "p.3" for a PDF or "section 3" for Word
    score: float

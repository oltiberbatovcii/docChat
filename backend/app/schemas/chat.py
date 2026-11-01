from pydantic import BaseModel, ConfigDict, Field


class ChatRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)  # so "   " counts as empty

    question: str = Field(min_length=1, max_length=1000)
    # Capped lower than /search: Ollama silently cuts off prompts beyond its context window
    top_k: int = Field(default=3, ge=1, le=10)


class SourceOut(BaseModel):
    filename: str
    page: int
    snippet: str


class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceOut]

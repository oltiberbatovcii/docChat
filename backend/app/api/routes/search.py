"""Semantic search over uploaded documents (retrieval only, no LLM)."""

from fastapi import APIRouter

from app.api.deps import VectorStoreDep
from app.schemas.search import SearchRequest, SearchResultOut

router = APIRouter(prefix="/search", tags=["search"])


@router.post("")
def search(request: SearchRequest, store: VectorStoreDep) -> list[SearchResultOut]:
    results = store.query(request.query, request.top_k)
    return [
        SearchResultOut(
            text=result.text, filename=result.filename, page=result.page, score=result.score
        )
        for result in results
    ]

"""Full RAG: answer a question from the uploaded documents, with citations."""

from dataclasses import asdict

from fastapi import APIRouter, HTTPException, status

from app.api.deps import GenerateDep, SettingsDep, VectorStoreDep
from app.prompts.answer_prompts import PROMPTS
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.llm import LLMError
from app.services.rag import answer_question

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("")
def chat(
    request: ChatRequest, store: VectorStoreDep, generate: GenerateDep, settings: SettingsDep
) -> ChatResponse:
    prompt = PROMPTS[settings.prompt_version]
    try:
        result = answer_question(request.question, request.top_k, store, generate, prompt)
    except LLMError as error:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "The language model is unavailable. Is Ollama running?",
        ) from error
    return ChatResponse(**asdict(result))

from fastapi import APIRouter, HTTPException

from app.config import settings
from app.core.history import load_history, save_chat
from app.core.llm import NOT_FOUND_ANSWER, answer_question
from app.core.retrieval import search
from app.logging import logger
from app.models.schemas import ChatRequest, ChatResponse, Citation, HistoryEntry, PageRef

router = APIRouter()


def _save_history(request: ChatRequest, response: ChatResponse) -> None:
    try:
        save_chat(request.document_id, request.question, response)
    except Exception:
        logger.exception("Failed to save chat history")


def _cited_pages(document_id: str, citations: list[Citation]) -> list[PageRef]:
    pages: set[int] = set()
    for citation in citations:
        if isinstance(citation.page_number, int):
            pages.add(citation.page_number)
        elif isinstance(citation.page_number, list):
            pages.update(citation.page_number)
    return [
        PageRef(page=page, image_url=f"/documents/{document_id}/pages/{page}")
        for page in sorted(pages)
    ]


@router.post("", response_model=ChatResponse)
async def ask_question(request: ChatRequest) -> ChatResponse:
    if not settings.google_api_key:
        raise HTTPException(status_code=503, detail="GOOGLE_API_KEY is not configured.")

    citations = search(request.document_id, request.question, collection=request.collection)
    if not citations:
        response = ChatResponse(answer=NOT_FOUND_ANSWER, citations=[], found_in_document=False)
        _save_history(request, response)
        return response

    try:
        answer = answer_question(request.question, citations)
    except Exception:
        logger.exception("LLM call failed")
        raise HTTPException(status_code=502, detail="LLM request failed.")

    found = NOT_FOUND_ANSWER.rstrip(".").lower() not in answer.lower()
    response = ChatResponse(
        answer=answer,
        citations=citations if found else [],
        pages=_cited_pages(request.document_id, citations) if found else [],
        found_in_document=found,
    )
    _save_history(request, response)
    return response


@router.get("/history", response_model=list[HistoryEntry])
async def get_history(document_id: str | None = None, limit: int = 50) -> list[HistoryEntry]:
    """Load recent chat history, newest first, optionally filtered by document_id."""
    try:
        entries = load_history(document_id=document_id, limit=min(limit, 200))
    except Exception:
        logger.exception("Failed to load chat history")
        raise HTTPException(status_code=503, detail="History storage unavailable.")
    return [HistoryEntry(**entry) for entry in entries]

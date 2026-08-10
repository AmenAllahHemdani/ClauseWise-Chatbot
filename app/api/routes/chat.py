from fastapi import APIRouter, HTTPException

from app.config import settings
from app.core.llm import NOT_FOUND_ANSWER, answer_question
from app.core.retrieval import search
from app.logging import logger
from app.models.schemas import ChatRequest, ChatResponse, Citation, PageRef

router = APIRouter()


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
        return ChatResponse(answer=NOT_FOUND_ANSWER, citations=[], found_in_document=False)

    try:
        answer = answer_question(request.question, citations)
    except Exception:
        logger.exception("LLM call failed")
        raise HTTPException(status_code=502, detail="LLM request failed.")

    found = NOT_FOUND_ANSWER.rstrip(".").lower() not in answer.lower()
    return ChatResponse(
        answer=answer,
        citations=citations if found else [],
        pages=_cited_pages(request.document_id, citations) if found else [],
        found_in_document=found,
    )

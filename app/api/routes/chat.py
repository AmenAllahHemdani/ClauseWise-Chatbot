from fastapi import APIRouter, HTTPException

from app.models.schemas import ChatRequest, ChatResponse

router = APIRouter()


@router.post("", response_model=ChatResponse)
async def ask_question(request: ChatRequest) -> ChatResponse:
    # TODO(epic-1): retrieve top chunks from Qdrant, answer with Gemini using the
    # grounded-only prompt ("answer only from the document, say 'not found' otherwise"),
    # and return citations pointing at the exact clauses.
    raise HTTPException(status_code=501, detail="Q&A not implemented yet (Epic 1).")

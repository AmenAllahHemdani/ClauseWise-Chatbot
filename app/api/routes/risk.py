from fastapi import APIRouter, HTTPException

from app.config import settings
from app.core.llm import scan_risks
from app.core.retrieval import get_document_chunks
from app.logging import logger
from app.models.schemas import RiskScanResponse

router = APIRouter()


@router.post("/{document_id}", response_model=RiskScanResponse)
async def scan_document(document_id: str, collection: str | None = None) -> RiskScanResponse:
    """Scan every indexed clause of a document for risky terms."""
    if not settings.google_api_key:
        raise HTTPException(status_code=503, detail="GOOGLE_API_KEY is not configured.")

    chunks = get_document_chunks(document_id, collection=collection)
    if not chunks:
        raise HTTPException(status_code=404, detail=f"No indexed chunks found for document '{document_id}'.")

    try:
        findings = scan_risks(chunks)
    except Exception:
        logger.exception("Risk scan LLM call failed")
        raise HTTPException(status_code=502, detail="LLM request failed.")

    logger.info(f"Risk scan of {document_id}: {len(findings)} findings from {len(chunks)} chunks")
    return RiskScanResponse(document_id=document_id, findings=findings)

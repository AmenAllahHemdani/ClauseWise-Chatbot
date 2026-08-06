from fastapi import APIRouter, HTTPException

from app.models.schemas import RiskScanResponse

router = APIRouter()


@router.post("/{document_id}", response_model=RiskScanResponse)
async def scan_document(document_id: str) -> RiskScanResponse:
    # TODO(epic-2): run the risk taxonomy scan (auto-renewal, indemnification, liability caps,
    # termination, non-compete, ...) with structured outputs and severity ratings.
    raise HTTPException(status_code=501, detail="Risk scan not implemented yet (Epic 2).")

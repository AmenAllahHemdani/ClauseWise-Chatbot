from enum import Enum

from pydantic import BaseModel


class DocumentStatus(str, Enum):
    uploaded = "uploaded"
    indexed = "indexed"
    failed = "failed"


class UploadResponse(BaseModel):
    document_id: str
    filename: str
    status: DocumentStatus


class Citation(BaseModel):
    chunk_id: str
    section: str | None = None
    page_number: int | list[int] | None = None
    text: str
    score: float


class PageRef(BaseModel):
    page: int
    image_url: str


class ChatRequest(BaseModel):
    document_id: str
    question: str
    collection: str | None = None  # defaults to settings.qdrant_collection


class ChatResponse(BaseModel):
    answer: str
    citations: list[Citation]
    pages: list[PageRef] = []
    found_in_document: bool


class RiskSeverity(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class RiskFinding(BaseModel):
    clause_type: str
    severity: RiskSeverity
    excerpt: str
    explanation: str
    section: str | None = None


class RiskScanResponse(BaseModel):
    document_id: str
    findings: list[RiskFinding]

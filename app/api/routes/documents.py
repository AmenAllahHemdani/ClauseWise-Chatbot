import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile

from app.config import settings
from app.core.pipeline import pipeline_document
from app.models.schemas import DocumentStatus, UploadResponse

router = APIRouter()


ALLOWED_EXTENSIONS = {".pdf", ".docx"}


@router.post("/upload", response_model=UploadResponse)
async def upload_document(collection : str ,file: UploadFile) -> UploadResponse:
    extension = Path(file.filename or "").suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported file type '{extension}'. Use PDF or DOCX.")

    contents = await file.read()
    if len(contents) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"File exceeds {settings.max_upload_mb} MB limit.")
    document_id = uuid.uuid4().hex
    pipeline_document(contents, file.filename or f"upload{extension}", document_id, collection)
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    destination = settings.upload_dir / f"{document_id}{extension}"
    destination.write_bytes(contents)

    return UploadResponse(document_id=document_id, filename=file.filename or destination.name, status=DocumentStatus.uploaded)

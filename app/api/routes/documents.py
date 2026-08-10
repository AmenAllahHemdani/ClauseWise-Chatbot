import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException, Response, UploadFile

from app.config import settings
from app.core.pipeline import pipeline_document
from app.models.schemas import DocumentStatus, UploadResponse

router = APIRouter()


ALLOWED_EXTENSIONS = {".pdf", ".docx"}


@router.get("/{document_id}/pages/{page_number}")
def get_page_image(document_id: str, page_number: int) -> Response:
    """Render one page of a stored document as a PNG image (pages are 1-based)."""
    import fitz  # pymupdf

    pdf_path = settings.upload_dir / f"{document_id}.pdf"
    if not pdf_path.is_file():
        matches = list(settings.upload_dir.glob(f"{document_id}.*"))
        if matches:
            raise HTTPException(status_code=400, detail="Page images are only available for PDF documents.")
        raise HTTPException(status_code=404, detail=f"Document '{document_id}' not found.")

    with fitz.open(pdf_path) as doc:
        if not 1 <= page_number <= len(doc):
            raise HTTPException(status_code=404, detail=f"Page {page_number} not found (document has {len(doc)} pages).")
        pixmap = doc[page_number - 1].get_pixmap(dpi=150)
        image = pixmap.tobytes("png")

    return Response(content=image, media_type="image/png")


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

"""PDF/DOCX -> structured text extraction.

Epic 1: use pymupdf for PDFs (text, headings, tables) and python-docx for DOCX.
Output preserves document structure (headings, section numbers) so chunking.py
can split by legal sections instead of fixed token windows.
"""

from dataclasses import dataclass, field
from pathlib import Path

from app.logging import logger


@dataclass
class ParsedBlock:
    text: str
    page: int | None = None
    heading: str | None = None


@dataclass
class ParsedDocument:
    filename: str
    blocks: list[ParsedBlock] = field(default_factory=list)
    text: str = ""


def parse_document(contents: bytes, filename: str) -> ParsedDocument:
    suffix = Path(filename).suffix.lower()
    if suffix == ".pdf":
        return _parse_pdf(contents, filename)
    if suffix == ".docx":
        return _parse_docx(contents, filename)
    raise ValueError(f"Unsupported file type: {suffix}")


def _parse_pdf(contents: bytes, filename: str) -> ParsedDocument:
    import fitz  # pymupdf

    logger.info(f"Parsing PDF document: {filename}")
    with fitz.open(stream=contents, filetype="pdf") as doc:
        text = ""
        blocks = []
        for page in doc:
            page_text = page.get_text()
            text += page_text
            blocks.append(ParsedBlock(text=page_text, page=page.number + 1))
    return ParsedDocument(filename=filename, text=text, blocks=blocks)


def _parse_docx(contents: bytes, filename: str) -> ParsedDocument:
    import docx

    raise NotImplementedError("TODO(epic-1): extract paragraphs/headings with python-docx")

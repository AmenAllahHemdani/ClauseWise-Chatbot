from app.core.parsing import ParsedDocument
from app.logging import logger
from app.utils.chunking import find_section_count, find_numbers_count, split_by_section, split_by_numbers, split_text


def chunk_document(document: ParsedDocument) -> list[str]:
    # merge tiny fragments, split oversized clauses with overlap, and carry section labels.
    logger.info(f"Chunking document: {document.filename}")

    section_count = find_section_count(document.text)
    numbers_count = find_numbers_count(document.text)

    if section_count > numbers_count:
        logger.debug(f"Chunking by sections: {section_count}")
        return split_by_section(document.text)
    elif numbers_count > section_count:
        logger.debug(f"Chunking by numbers: {numbers_count}")
        return split_by_numbers(document.text)
    else:
        logger.debug(f"Chunking by default: {section_count} sections, {numbers_count} numbers")
        return split_text(document.text)


def chunk_pages(document: ParsedDocument, chunks: list[str]) -> list[int | list[int] | None]:
    """Map each chunk back to the page(s) its text came from.

    document.text is the concatenation of the per-page block texts, and every
    chunk is a contiguous substring of it, so a chunk's character span can be
    intersected with the page spans. Returns, per chunk: a single page number,
    a list of page numbers when the chunk straddles pages, or None when the
    chunk can't be located (e.g. DOCX documents have no page blocks).
    """
    page_spans = []
    offset = 0
    for block in document.blocks:
        page_spans.append((offset, offset + len(block.text), block.page))
        offset += len(block.text)

    pages_per_chunk: list[int | list[int] | None] = []
    # chunks come in document order, so advance a search cursor to resolve
    # repeated fragments to the right occurrence
    cursor = 0
    for chunk in chunks:
        start = document.text.find(chunk, cursor)
        if start == -1:
            start = document.text.find(chunk)
        if start == -1:
            pages_per_chunk.append(None)
            continue
        cursor = start + 1
        end = start + len(chunk)
        pages = [
            page
            for span_start, span_end, page in page_spans
            if page is not None and span_start < end and start < span_end
        ]
        if not pages:
            pages_per_chunk.append(None)
        elif len(pages) == 1:
            pages_per_chunk.append(pages[0])
        else:
            pages_per_chunk.append(pages)
    return pages_per_chunk
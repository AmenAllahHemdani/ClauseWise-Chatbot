import re

from app.core.parsing import ParsedDocument
from app.logging import logger
from app.utils.chunking import find_section_count, find_numbers_count, split_by_section, split_by_numbers, split_text


def chunk_document(document: ParsedDocument) -> list[str]:
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


def chunk_spans(document: ParsedDocument, chunks: list[str]) -> list[tuple[int, int] | None]:
    """
    Locate each chunk's (start, end) character span in document.text.
    """

    spans: list[tuple[int, int] | None] = []
    cursor = 0
    for chunk in chunks:
        start = document.text.find(chunk, cursor)
        if start == -1:
            start = document.text.find(chunk)
        if start == -1:
            spans.append(None)
            continue
        cursor = start + 1
        spans.append((start, start + len(chunk)))
    return spans


def chunk_pages(document: ParsedDocument, chunks: list[str]) -> list[int | list[int] | None]:
    """
    Map each chunk back to the page(s) its text came from.
    """

    page_spans = []
    offset = 0
    for block in document.blocks:
        page_spans.append((offset, offset + len(block.text), block.page))
        offset += len(block.text)

    pages_per_chunk: list[int | list[int] | None] = []
    for span in chunk_spans(document, chunks):
        if span is None:
            pages_per_chunk.append(None)
            continue
        start, end = span
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


# "7" / "1.1" / "5.2 - 5.4"
_RULE_BEFORE_CHUNK = re.compile(
    r"(?i)(?:\bsection\s+(?P<section>\d+)|\n\n(?P<number>\d+(?:\.\d+)?(?:\s*-\s*\d+(?:\.\d+)?)?))\s*$"
)
# a lettered sub-clause marker like "(a)" right before a chunk
_LETTER_BEFORE_CHUNK = re.compile(r"\(([a-z])\)\s*$")

_PARENT_MARKERS = re.compile(
    r"(?i)\bsection\s+(?P<section>\d+)|\n\n(?P<number>\d+(?:\.\d+)?(?:\s*-\s*\d+(?:\.\d+)?)?)"
)


def chunk_rules(document: ParsedDocument, chunks: list[str]) -> list[str | None]:
    """
    Recover the rule/clause number each chunk was split on.
    """

    parent_markers = [
        (match.start(), re.sub(r"\s+", "", match.group("section") or match.group("number")))
        for match in _PARENT_MARKERS.finditer(document.text)
    ]

    rules: list[str | None] = []
    for span in chunk_spans(document, chunks):
        if span is None:
            rules.append(None)
            continue
        start, _ = span
        window = document.text[max(0, start - 40):start]

        match = _RULE_BEFORE_CHUNK.search(window)
        if match is not None:
            rules.append(re.sub(r"\s+", "", match.group("section") or match.group("number")))
            continue

        letter = _LETTER_BEFORE_CHUNK.search(window)
        if letter is None:
            rules.append(None)
            continue
        parent = None
        for position, label in parent_markers:
            if position < start:
                parent = label
            else:
                break
        rules.append(f"{parent} ({letter.group(1)})" if parent else f"({letter.group(1)})")
    return rules
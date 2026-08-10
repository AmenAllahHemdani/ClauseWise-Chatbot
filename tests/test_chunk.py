from pathlib import Path

import pytest

from app.utils.chunking import (
    find_numbers_count,
    find_section_count,
    split_by_numbers,
    split_by_section,
    split_text,
)

SAMPLES_DIR = Path(__file__).resolve().parent.parent / "data" / "samples"


def test_split_by_numbers_plain_text():
    text = "1. Employee duties are defined here.\n2. Compensation is described here."
    chunks = split_by_numbers(text)
    assert len(chunks) == 2
    assert "Employee duties" in chunks[0]
    assert "Compensation" in chunks[1]


def test_split_by_numbers_empty_input():
    assert split_by_numbers("") == []
    assert split_by_numbers(None) == []


def test_split_by_section_plain_text():
    text = "Preamble text.\nSection 1 covers scope.\nSection 2 covers payment."
    chunks = split_by_section(text)
    assert len(chunks) == 3
    assert "covers payment" in chunks[-1]


def test_find_counts():
    text = "Section 1 has clause 1.1 and clause 1.2. Section 2 has clause 2.1."
    assert find_section_count(text) == 2
    assert find_numbers_count(text) >= 4


def test_split_text_chunks_within_size():
    text = "This is a sentence about contracts. " * 50
    chunks = split_text(text, chunk_size=200, chunk_overlap=50)
    assert chunks
    assert all(len(chunk) <= 200 for chunk in chunks)


def test_split_text_rejects_empty_input():
    with pytest.raises(ValueError):
        split_text("")


def test_chunk_pages_single_multi_and_missing():
    from app.core.chunking import chunk_pages
    from app.core.parsing import ParsedBlock, ParsedDocument

    page1 = "Alpha clause text. "
    page2 = "Beta clause text."
    doc = ParsedDocument(
        filename="x.pdf",
        text=page1 + page2,
        blocks=[ParsedBlock(text=page1, page=1), ParsedBlock(text=page2, page=2)],
    )
    chunks = ["Alpha clause", "text. Beta", "Beta clause text.", "not in the document"]
    assert chunk_pages(doc, chunks) == [1, [1, 2], 2, None]


def test_chunk_pages_repeated_fragment_resolves_in_order():
    from app.core.chunking import chunk_pages
    from app.core.parsing import ParsedBlock, ParsedDocument

    page1 = "clause, and more. "
    page2 = "clause, again."
    doc = ParsedDocument(
        filename="x.pdf",
        text=page1 + page2,
        blocks=[ParsedBlock(text=page1, page=1), ParsedBlock(text=page2, page=2)],
    )
    # the same fragment appears on both pages; order decides which occurrence
    assert chunk_pages(doc, ["clause,", "clause,"]) == [1, 2]


def test_chunk_rules_numbers_and_sections():
    from app.core.chunking import chunk_rules
    from app.core.parsing import ParsedBlock, ParsedDocument
    from app.utils.chunking import split_by_numbers, split_by_section

    numbered = "Preamble here.\n1.1 First rule text.\n1.2 Second rule text.\n2 Third rule text."
    doc = ParsedDocument(filename="x.pdf", text=numbered, blocks=[ParsedBlock(text=numbered, page=1)])
    chunks = split_by_numbers(numbered)
    assert chunk_rules(doc, chunks) == [None, "1.1", "1.2", "2"]

    sectioned = "Preamble here.\nSection 1 covers scope.\nSection 12 covers payment."
    doc = ParsedDocument(filename="x.pdf", text=sectioned, blocks=[ParsedBlock(text=sectioned, page=1)])
    chunks = split_by_section(sectioned)
    assert chunk_rules(doc, chunks) == [None, "1", "12"]


def test_chunk_rules_lettered_subclauses():
    from app.core.chunking import chunk_rules
    from app.core.parsing import ParsedBlock, ParsedDocument
    from app.utils.chunking import split_by_numbers

    text = (
        "Preamble.\n"
        "1 Duties are the following.\n"
        "(a) First duty text.\n"
        "(b) Second duty text.\n"
        "2 Compensation follows.\n"
        "(a) Base salary text."
    )
    doc = ParsedDocument(filename="x.pdf", text=text, blocks=[ParsedBlock(text=text, page=1)])
    chunks = split_by_numbers(text)
    assert chunks == [
        "Preamble.",
        "Duties are the following.",
        "First duty text.",
        "Second duty text.",
        "Compensation follows.",
        "Base salary text.",
    ]
    assert chunk_rules(doc, chunks) == [None, "1", "1 (a)", "1 (b)", "2", "2 (a)"]


def test_chunk_sample_pdf():
    pytest.importorskip("fitz", reason="pymupdf not installed")
    from app.core.chunking import chunk_document
    from app.core.parsing import parse_document

    pdf_path = SAMPLES_DIR / "employment_agreement.pdf"
    parsed = parse_document(pdf_path.read_bytes(), pdf_path.name)
    assert parsed.filename == "employment_agreement.pdf"
    assert parsed.text.strip()

    chunks = chunk_document(parsed)
    assert chunks
    assert all(isinstance(chunk, str) and chunk.strip() for chunk in chunks)

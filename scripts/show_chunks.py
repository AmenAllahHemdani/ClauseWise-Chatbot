"""Print the chunk list for a contract PDF/DOCX in the terminal, no server needed.

Usage:
    python scripts/show_chunks.py [path/to/document.pdf] [--full]

Defaults to data/samples/employment_agreement.pdf. Chunks are truncated to one
preview line each; pass --full to print the entire text of every chunk.
"""

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.core.chunking import chunk_document, chunk_pages, chunk_rules
from app.core.parsing import parse_document


def main() -> None:
    parser = argparse.ArgumentParser(description="Parse a document and print its chunks.")
    parser.add_argument(
        "path",
        type=Path,
        nargs="?",
        default=PROJECT_ROOT / "data" / "samples" / "employment_agreement.pdf",
        help="PDF or DOCX file to chunk",
    )
    parser.add_argument("--full", action="store_true", help="print full chunk text instead of a preview")
    args = parser.parse_args()

    if not args.path.is_file():
        sys.exit(f"File not found: {args.path}")

    parsed = parse_document(args.path.read_bytes(), args.path.name)
    chunks = chunk_document(parsed)
    pages_per_chunk = chunk_pages(parsed, chunks)
    rules_per_chunk = chunk_rules(parsed, chunks)

    for i, (chunk, pages, rule) in enumerate(zip(chunks, pages_per_chunk, rules_per_chunk)):
        page_label = "p.?" if pages is None else f"p.{pages}"
        rule_label = "rule -" if rule is None else f"rule {rule}"
        if args.full:
            print(f"--- chunk {i} ({page_label}, {rule_label}, {len(chunk)} chars) ---")
            print(chunk)
        else:
            preview = " ".join(chunk.split())
            print(f"[{i:3}] {page_label:12} {rule_label:10} ({len(chunk):5} chars) {preview[:90]}")

    print(f"\n{len(chunks)} chunks from {args.path.name}")


if __name__ == "__main__":
    main()

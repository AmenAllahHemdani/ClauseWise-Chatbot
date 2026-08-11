"""Gemini client and prompts (grounded Q&A, risk scan)."""

from functools import lru_cache
from typing import Any, Dict, List

from app.config import settings
from app.logging import logger
from app.models.schemas import Citation, RiskFinding

GROUNDED_QA_SYSTEM_PROMPT = """\
You are a contract analysis assistant. Answer the user's question using ONLY the
provided contract excerpts. Quote the relevant clause when possible.
If the answer is not in the excerpts, reply exactly: "Not found in the document."
Never use outside knowledge about laws or typical contracts to fill gaps.
"""


@lru_cache(maxsize=1)
def _client():
    from google import genai

    return genai.Client(api_key=settings.google_api_key)


NOT_FOUND_ANSWER = "Not found in the document."


def answer_question(question: str, citations: list[Citation]) -> str:
    from google.genai import types

    excerpts = "\n\n".join(
        f"[{i}] (clause {citation.section or 'unknown'}) {citation.text}"
        for i, citation in enumerate(citations, 1)
    )
    response = _client().models.generate_content(
        model=settings.llm_model,
        contents=f"Contract excerpts:\n\n{excerpts}\n\nQuestion: {question}",
        config=types.GenerateContentConfig(
            system_instruction=GROUNDED_QA_SYSTEM_PROMPT,
            temperature=0,
        ),
    )
    return (response.text or NOT_FOUND_ANSWER).strip()


RISK_SCAN_SYSTEM_PROMPT = """\
You are a legal risk analyst reviewing a contract on behalf of the party who
received it (not the party who drafted it). Scan the provided clauses and report
risky or unusual terms. Watch for, among others: auto-renewal, indemnification,
uncapped or one-sided liability, broad termination rights, non-compete or
non-solicitation, unilateral changes, penalties and interest, repayment
obligations, IP assignment, confidentiality, payment terms, and governing
law / jurisdiction.

For each finding:
- clause_type: short label like "auto-renewal" or "indemnification"
- severity: low, medium, or high, judged by potential impact on the receiving party
- excerpt: a short verbatim quote from the clause (trim with "..." if long)
- explanation: one or two sentences on why this is a risk
- section: the clause number only, copied from the "clause:" tag before the
  excerpt (e.g. "2.01 (a)" or "4"); null if the tag says General or unknown.
  Never include the word "clause" or the page in this field.

Only report clauses actually present in the excerpts; never invent text.
Return an empty list if nothing risky is found.
"""

# stay well inside the model's context window even for very large contracts
_MAX_SCAN_CHARS = 150_000


def scan_risks(chunks: List[Dict[str, Any]]) -> List[RiskFinding]:
    from google.genai import types

    excerpts = []
    total = 0
    for chunk in chunks:
        label = chunk.get("rule_number") or chunk.get("section_title") or "?"
        page = chunk.get("page_number")
        block = f"[clause: {label} | page: {page}] {chunk.get('content', '')}"
        total += len(block)
        if total > _MAX_SCAN_CHARS:
            logger.warning(f"Risk scan truncated at {_MAX_SCAN_CHARS} chars ({len(excerpts)}/{len(chunks)} chunks sent)")
            break
        excerpts.append(block)

    response = _client().models.generate_content(
        model=settings.llm_model,
        contents="Contract clauses:\n\n" + "\n\n".join(excerpts),
        config=types.GenerateContentConfig(
            system_instruction=RISK_SCAN_SYSTEM_PROMPT,
            temperature=0,
            response_mime_type="application/json",
            response_schema=list[RiskFinding],
        ),
    )
    return response.parsed or []

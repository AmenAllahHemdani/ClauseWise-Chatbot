"""Gemini client and prompts (grounded Q&A, risk scan)."""

from functools import lru_cache

from app.config import settings
from app.models.schemas import Citation

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

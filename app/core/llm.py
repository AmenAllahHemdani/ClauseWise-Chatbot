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


def answer_question(question: str, citations: list[Citation]) -> str:
    # TODO(epic-1): build the excerpts block from citations and call
    # _client().models.generate_content(model=settings.llm_model, ...).
    raise NotImplementedError

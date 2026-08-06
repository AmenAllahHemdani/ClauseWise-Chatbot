"""Embedding pipeline (fastembed — local, no API key)."""

from functools import lru_cache

from app.config import settings
from sentence_transformers import SentenceTransformer
from app.logging import logger

@lru_cache(maxsize=1)
def _embedding_model():
    logger.info(f"Loading embedding model: {settings.embedding_model}")
    return SentenceTransformer(settings.embedding_model)


def embed_text(text: str) -> list[list[float]]:
    return  _embedding_model().encode(text, show_progress_bar=True)


def embed_chunks(chunks: list[str]) -> list[list[float]]:
    return _embedding_model().encode(chunks, show_progress_bar=True)
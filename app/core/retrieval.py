"""Qdrant indexing + search, and citation assembly."""

from functools import lru_cache

from app.config import settings
from app.core.chunking import Chunk
from app.models.schemas import Citation


@lru_cache(maxsize=1)
def _client():
    from qdrant_client import QdrantClient

    return QdrantClient(url=settings.qdrant_url)


def index_chunks(document_id: str, chunks: list[Chunk]) -> None:
    # TODO(epic-1): ensure collection exists, embed chunks, upsert points with
    # payload {document_id, section, page, text}.
    raise NotImplementedError


def search(document_id: str, query: str, limit: int = 6) -> list[Citation]:
    # TODO(epic-1): embed query, search filtered by document_id, map hits to Citations.
    raise NotImplementedError

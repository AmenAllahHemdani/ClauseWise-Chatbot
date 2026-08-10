"""Qdrant search and citation assembly."""

from functools import lru_cache

from app.config import settings
from app.core.vector_store import VectorStore
from app.models.schemas import Citation


@lru_cache(maxsize=4)
def _store(collection: str) -> VectorStore:
    return VectorStore(
        collection_name=collection,
        model_name=settings.embedding_model,
        location=settings.qdrant_url,
    )


def search(
    document_id: str,
    query: str,
    limit: int = 6,
    collection: str | None = None,
) -> list[Citation]:
    """Search a contract's chunks and map the hits to Citations."""
    store = _store(collection or settings.qdrant_collection)
    hits = store.search_contract(query, contract_id=document_id, top_k=limit)
    return [
        Citation(
            chunk_id=hit["chunk_id"],
            section=hit.get("rule_number") or hit.get("section_title"),
            page_number=hit.get("page_number"),
            text=hit["content"],
            score=hit["score"],
        )
        for hit in hits
    ]

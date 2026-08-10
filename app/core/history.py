"""Chat history persistence in MongoDB."""

from datetime import datetime, timezone
from functools import lru_cache
from typing import Any, Dict, List, Optional

from pymongo import ASCENDING, DESCENDING, MongoClient

from app.config import settings
from app.models.schemas import ChatResponse


@lru_cache(maxsize=1)
def _collection():
    if not settings.mongo_url:
        raise RuntimeError("MONGO_URL is not configured.")
    client = MongoClient(settings.mongo_url, serverSelectionTimeoutMS=5000)
    collection = client[settings.mongo_db]["chat_history"]
    collection.create_index([("document_id", ASCENDING), ("created_at", DESCENDING)])
    return collection


def save_chat(document_id: str, question: str, response: ChatResponse) -> str:
    entry = {
        "document_id": document_id,
        "question": question,
        "answer": response.answer,
        "found_in_document": response.found_in_document,
        "citations": [citation.model_dump() for citation in response.citations],
        "pages": [page.model_dump() for page in response.pages],
        "created_at": datetime.now(timezone.utc),
    }
    result = _collection().insert_one(entry)
    return str(result.inserted_id)


def load_history(document_id: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
    """Most recent chat entries first, optionally filtered by document."""
    query = {"document_id": document_id} if document_id else {}
    entries = []
    for entry in _collection().find(query).sort("created_at", DESCENDING).limit(limit):
        entry["id"] = str(entry.pop("_id"))
        entry["created_at"] = entry["created_at"].isoformat()
        entries.append(entry)
    return entries

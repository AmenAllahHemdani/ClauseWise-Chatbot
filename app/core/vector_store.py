import uuid
from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, Field
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
    PayloadSchemaType,
)


class ContractChunk(BaseModel):
    """Data model representing a chunk of contract text."""
    content: str
    contract_id: str
    page_number: Optional[Union[int, List[int]]] = None
    rule_number: Optional[str] = None
    section_title: Optional[str] = "General"
    chunk_id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))


class VectorStore:
    """Vector store wrapper around Qdrant for legal contract management."""

    def __init__(
        self,
        collection_name: str = "clausewise_contracts",
        model_name: str = "BAAI/bge-small-en-v1.5",
        location: str = ":memory:",  # ":memory:", "./qdrant_db", or "http://localhost:6333"
        api_key: Optional[str] = None,
    ):
        self.collection_name = collection_name
        
        self.embedding_model = SentenceTransformer(model_name)
        self.embedding_dim = self.embedding_model.get_sentence_embedding_dimension()
        
        self.is_bge_model = "bge" in model_name.lower()

        if location.startswith("http://") or location.startswith("https://"):
            self.client = QdrantClient(url=location, api_key=api_key)
        elif location == ":memory:":
            self.client = QdrantClient(location=":memory:")
        else:
            self.client = QdrantClient(path=location)

        self._ensure_collection_exists()

    def _ensure_collection_exists(self) -> None:
        """Creates collection if it doesn't exist and sets up payload indexing."""
        collections = [c.name for c in self.client.get_collections().collections]
        
        if self.collection_name not in collections:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.embedding_dim,
                    distance=Distance.COSINE,
                ),
            )
            
            self.client.create_payload_index(
                collection_name=self.collection_name,
                field_name="contract_id",
                field_schema=PayloadSchemaType.KEYWORD,
            )

    def save_embed(
        self,
        chunks: List[ContractChunk],
        vectors: List[List[float]],
        extra_payload: Optional[Dict[str, Any]] = None,
    ) -> List[str]:
        """
        Saves pre-computed embedding vectors along with their ContractChunk metadata into Qdrant.

        Args:
            chunks: ContractChunk objects containing metadata (text, page, section, contract_id).
            vectors: One pre-generated embedding vector per chunk, in the same order.
            extra_payload: Optional dict for additional custom metadata (e.g., risk_level, clause_type)
                applied to every chunk.

        Returns:
            The chunk_ids (Point IDs) saved in Qdrant.
        """
        if len(chunks) != len(vectors):
            raise ValueError(
                f"Got {len(chunks)} chunks but {len(vectors)} vectors."
            )

        points = []
        for chunk, vector in zip(chunks, vectors):
            if len(vector) != self.embedding_dim:
                raise ValueError(
                    f"Vector dimension mismatch! Expected {self.embedding_dim}, got {len(vector)}."
                )

            payload = {
                "content": chunk.content,
                "contract_id": chunk.contract_id,
                "page_number": chunk.page_number,
                "rule_number": chunk.rule_number,
                "section_title": chunk.section_title,
            }
            if extra_payload:
                payload.update(extra_payload)

            points.append(
                PointStruct(
                    id=chunk.chunk_id,
                    vector=list(vector),
                    payload=payload,
                )
            )

        self.client.upsert(
            collection_name=self.collection_name,
            points=points,
        )

        return [chunk.chunk_id for chunk in chunks]

    def add_chunks(self, chunks: List[ContractChunk]) -> int:
        """Embeds contract text chunks automatically and upserts them into Qdrant."""
        if not chunks:
            return 0

        texts = [chunk.content for chunk in chunks]
        
        embeddings = self.embedding_model.encode(
            texts, 
            normalize_embeddings=True, 
            show_progress_bar=False
        )

        points = []
        for chunk, embedding in zip(chunks, embeddings):
            points.append(
                PointStruct(
                    id=chunk.chunk_id,
                    vector=embedding.tolist(),
                    payload={
                        "content": chunk.content,
                        "contract_id": chunk.contract_id,
                        "page_number": chunk.page_number,
                        "rule_number": chunk.rule_number,
                        "section_title": chunk.section_title,
                    },
                )
            )

        self.client.upsert(
            collection_name=self.collection_name,
            points=points,
        )
        return len(points)

    def get_contract_chunks(self, contract_id: str) -> List[Dict[str, Any]]:
        """All stored chunk payloads for one contract, ordered by page."""
        payloads = []
        offset = None
        while True:
            points, offset = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(
                            key="contract_id",
                            match=MatchValue(value=contract_id),
                        )
                    ]
                ),
                limit=256,
                offset=offset,
                with_payload=True,
            )
            payloads.extend(point.payload for point in points)
            if offset is None:
                break

        def first_page(payload: Dict[str, Any]) -> int:
            page = payload.get("page_number")
            if isinstance(page, list) and page:
                return page[0]
            return page if isinstance(page, int) else 0

        payloads.sort(key=first_page)
        return payloads

    def search_contract(
        self,
        query: str,
        contract_id: Optional[str] = None,
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """Searches the vector store for top matching legal clauses."""
        search_query = f"Represent this sentence for searching relevant passages: {query}" if self.is_bge_model else query
        
        query_vector = self.embedding_model.encode(
            search_query, 
            normalize_embeddings=True
        ).tolist()

        query_filter = None
        if contract_id:
            query_filter = Filter(
                must=[
                    FieldCondition(
                        key="contract_id",
                        match=MatchValue(value=contract_id),
                    )
                ]
            )

        search_results = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            query_filter=query_filter,
            limit=top_k,
        ).points

        formatted_hits = []
        for hit in search_results:
            formatted_hits.append(
                {
                    "chunk_id": str(hit.id),
                    "score": round(hit.score, 4),
                    "content": hit.payload.get("content"),
                    "contract_id": hit.payload.get("contract_id"),
                    "page_number": hit.payload.get("page_number"),
                    "rule_number": hit.payload.get("rule_number"),
                    "section_title": hit.payload.get("section_title"),
                    "payload": hit.payload,  # Returns full payload including extra metadata
                }
            )

        return formatted_hits
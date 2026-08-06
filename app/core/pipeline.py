from app.config import settings
from app.core.parsing import parse_document
from app.core.chunking import chunk_document, chunk_pages
from app.core.embeddings import embed_chunks
from app.logging import logger
from app.core.vector_store import ContractChunk, VectorStore

def pipeline_document(contents: bytes, filename: str, contract_id: str, collection : str) -> list[str]:
    parsed_document = parse_document(contents, filename)
    chunks = chunk_document(parsed_document)
    embeddings = embed_chunks(chunks)

    pages_per_chunk = chunk_pages(parsed_document, chunks)
    contract_chunks = [
        ContractChunk(content=chunk, contract_id=contract_id, page_number=pages)
        for chunk, pages in zip(chunks, pages_per_chunk)
    ]

    vector_store = VectorStore(
        collection_name=collection,
        model_name=settings.embedding_model,
        location=settings.qdrant_url,
    )
    vector_store.save_embed(contract_chunks, embeddings)

    logger.info(f"Document {parsed_document.filename} indexed with {len(chunks)} chunks")
    return chunks

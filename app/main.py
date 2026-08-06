from fastapi import FastAPI

from app.api.routes import chat, documents, risk

app = FastAPI(
    title="ClauseWise",
    version="0.1.0",
    description="Contract Q&A and review assistant — grounded answers with clause-level citations.",
)

app.include_router(documents.router, prefix="/documents", tags=["documents"])
app.include_router(chat.router, prefix="/chat", tags=["chat"])
app.include_router(risk.router, prefix="/risk", tags=["risk"])


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}

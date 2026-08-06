# ClauseWise ⚖️

Contract Q&A and review assistant. Upload a contract (PDF/DOCX), ask questions about it, get answers **with citations to the exact clause**, and run an automated risk scan for problematic terms.

## Features

- 📄 PDF/DOCX ingestion with structure-aware chunking (by legal sections/clauses, not fixed token windows)
- 💬 Grounded Q&A — answers cite the source clause, or say "not found in document"
- 🚨 Risk scan — flags auto-renewal, indemnification, liability caps, termination, non-compete clauses with severity ratings
- 🔀 Contract compare — what changed between two versions and does it matter

## Architecture

```
Streamlit UI ──► FastAPI ──► parsing (pymupdf) ──► clause-aware chunking
                    │
                    ├──► Qdrant (vector store) ◄── embeddings (fastembed, local)
                    └──► Gemini API (grounded answers, risk scan via structured outputs)
```

## Quickstart

```bash
# 1. Configure
cp .env.example .env        # then add your GOOGLE_API_KEY

# 2. Start the stack (API + Qdrant)
docker compose up --build

# 3. Or run locally against dockerized Qdrant
docker compose up -d qdrant
pip install -r requirements.txt
uvicorn app.main:app --reload

# 4. Streamlit UI
streamlit run ui/streamlit_app.py
```

API docs at http://localhost:8000/docs — Qdrant dashboard at http://localhost:6333/dashboard

## Project structure

```
app/
  main.py            # FastAPI entrypoint
  config.py          # settings from .env (pydantic-settings)
  api/routes/        # documents (upload), chat (Q&A), risk (scan)
  core/
    parsing.py       # PDF/DOCX → structured text (pymupdf)
    chunking.py      # structure-aware legal chunking
    embeddings.py    # embedding pipeline
    retrieval.py     # Qdrant search + citation assembly
    llm.py           # Gemini client, grounded-answer + risk-scan prompts
  models/schemas.py  # request/response + structured-output schemas
ui/streamlit_app.py  # upload / chat / risk report UI
eval/                # CUAD-based eval set + harness (retrieval hit rate, faithfulness)
data/samples/        # sample contracts for the live demo
tests/
```

## Evals

Measured on a ~30-question set built from public contracts (SEC EDGAR + CUAD labeled clauses):

| Metric | Result |
|---|---|
| Retrieval hit rate | _TBD_ |
| Answer faithfulness | _TBD_ |

See `eval/` for the harness.

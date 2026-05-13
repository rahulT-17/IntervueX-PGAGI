PGAGI Backend
=============

Production-minded MVP for a role-based AI interview system with a traceable RAG pipeline.

Repository Layout
-----------------
This repo keeps backend code inside `backend/`:

```
backend/
  app/
  data/
    docs/
  .env.example
  .gitignore
  requirements.txt
```

Quickstart
----------
1) Open terminal in repo root and move into backend:

   `cd backend`

2) Create and activate a venv (Python 3.12 recommended).

3) Install dependencies:

   `pip install -r requirements.txt`

4) Copy env file:

   `copy .env.example .env`

5) Run DB init once:

   `python -m app.db.run_init`

6) Run API:

   `uvicorn app.main:app --reload`

Configuration (.env)
--------------------
- `DATABASE_URL`: async Postgres URL (asyncpg)
- `RAG_DOCS_DIR`: docs folder for ingestion (default `data/docs`)
- `CHROMA_PERSIST_DIR`: local vector store path (default `data/chroma`)
- `LLM_BASE_URL`: OpenAI-compatible endpoint
- `LLM_MODEL`: model id

Current API Endpoints
---------------------
- `GET /api/v1/health`
- `POST /api/v1/interview/start`
- `POST /api/v1/rag/ingest`
- `POST /api/v1/rag/retrieve`
- `POST /api/v1/interview/question`
- `POST /api/v1/interview/answer`


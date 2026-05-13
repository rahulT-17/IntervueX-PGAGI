PGAGI Backend
=============

Production-minded MVP for a role-based AI interview system with a traceable RAG pipeline.

Project Idea
------------
Build an AI interview backend that can:
- ingest role-relevant documents,
- retrieve grounded context for interview generation,
- generate interview questions,
- evaluate candidate answers,
- and return a session summary with traceable retrieval evidence.

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
- `GET /api/v1/interview/{session_id}/summary?include_chunks=true|false`

Key Design Decisions I Made
---------------------------
- Modular backend by responsibility:
  API routes, DB layer, RAG pipeline, and LLM services are separated for maintainability.
- Traceability-first retrieval logging:
  Every retrieval stores generated query + retrieved chunks in `retrieval_logs`.
- Role-aware retrieval:
  Documents are tagged with role metadata and retrieval filters by role for better relevance.
- Strict request validation:
  `top_k` is bounded and list defaults use safe factories to avoid mutable default bugs.
- Mistral-compatible prompting:
  LLM calls use a single `user` message format to remain compatible with endpoints that do not support `system`.
- Resilient LLM JSON handling:
  LLM outputs are parsed and schema-validated before persistence/response to avoid brittle runtime failures.
- Evidence-preserving data model:
  Questions persist `source_chunks`, answers persist `generated_feedback`, and summary supports `include_chunks` toggle.


PGAGI Backend
=============

Production-minded MVP for a role-based AI interview system with a traceable RAG pipeline.

What This Is
------------
- FastAPI backend with async PostgreSQL and a modular RAG pipeline.
- Focus on traceability: every retrieval can be logged with query + chunks.
- Clean, minimal API surface for an interview flow.

Design Principles
-----------------
- One job per module: keep files focused (settings, db, rag, services).
- Traceability first: log the query + retrieved chunks for every question.
- Simple beats fancy: no agents, no hidden memory, no magic state.
- MVP discipline: prove the pipeline end-to-end before adding features.

System Flow (High Level)
------------------------
Resume Upload (Gate 1)
	-> Parse Skills
	-> Role Selection
	-> Retrieval Query
	-> RAG Retrieval
	-> Question Generation
	-> Interview Loop
	-> Summary

Current Status
--------------
- Gate 0: Foundation (done)
- Gate 2: RAG ingestion (done)
- Gate 3: Retrieval + logging (done)
- Gate 4: Question generation (done)
- Gate 1/5/6: in progress

Quickstart
----------
1) Create and activate a venv (Python 3.12 recommended).
2) Install dependencies:

	 pip install -r requirements.txt

3) Copy env file:

	 copy .env.example .env

4) Run the app:

	 uvicorn app.main:app --reload

Configuration (.env)
--------------------
- DATABASE_URL: async Postgres URL (asyncpg)
- RAG_DOCS_DIR: folder of PDFs/text to ingest
- CHROMA_PERSIST_DIR: where Chroma stores vectors
- LLM_BASE_URL: OpenAI-compatible URL (LM Studio or Groq)
- LLM_MODEL: model id from /v1/models

RAG Ingestion (Gate 2)
----------------------
1) Put docs in data/docs.
2) Call:

	 POST /api/v1/rag/ingest
	 {
		 "role": "backend",
		 "docs_path": "data/docs"
	 }

Expected response:
	{"documents": 1, "chunks": 2, "vectors": 2}

RAG Retrieval (Gate 3)
----------------------
1) Create an interview session.
2) Call:

	 POST /api/v1/rag/retrieve
	 {
		 "session_id": 1,
		 "role": "backend",
		 "skills": ["FastAPI", "SQLAlchemy", "PostgreSQL"],
		 "context": "Interview for mid-level backend engineer",
		 "top_k": 6
	 }

Retrieval logs are stored in retrieval_logs with query + chunks.

Question Generation (Gate 4)
-----------------------------
1) Ensure LLM server is running (LM Studio locally or Groq in deployment).
2) Call:

	 POST /api/v1/interview/question
	 {
		 "session_id": 1,
		 "role": "backend",
		 "skills": ["FastAPI", "SQLAlchemy", "PostgreSQL"],
		 "context": "Interview for mid-level backend engineer",
		 "top_k": 6
	 }

Returns:
- question
- topic
- difficulty
- source_chunks

API Endpoints (Current)
-----------------------
- GET /api/v1/health
- POST /api/v1/interview/start
- POST /api/v1/rag/ingest
- POST /api/v1/rag/retrieve
- POST /api/v1/interview/question

Data Model (Core Tables)
------------------------
- users
- interview_sessions
- questions (includes source_chunks)
- answers
- retrieval_logs (query + chunks)

Project Structure (Backend)
---------------------------
app/
	api/        API routes
	core/       settings and logging
	db/         async DB session
	models.py   SQLAlchemy models
	schemas.py  Pydantic schemas
	rag/        ingestion + retrieval
	services/   LLM client + generation

Notes
-----
- For large PDFs, consider OCR or clean-up to improve chunk quality.
- Smaller, curated docs yield better retrieval.


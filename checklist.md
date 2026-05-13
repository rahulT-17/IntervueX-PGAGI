Plan: End-to-End MVP Checklist + Next Step
Build a concise end-to-end MVP checklist with explicit gates, then begin the next build phase (RAG ingestion scaffold) so we can reach a minimal working pipeline quickly and verify each gate.

Steps

Create a new checklist file at the repository root (named as requested) that lists MVP tasks with explicit gates and acceptance criteria.
Gate 0: Foundation verified (app boots, health endpoint works, DB connection works, tables exist).
Gate 1: Resume intake stub (upload endpoint + simple parsing service that extracts skills/role hints; store in DB or session payload).
Gate 2: RAG ingestion scaffold (document loader + chunker + embedding stub + ChromaDB vector store initialization; store metadata for role/source).
Gate 3: Retrieval pipeline (dynamic query builder from role + skills + context; log query + retrieved chunks to retrieval_logs).
Gate 4: Question generation (generate question from retrieved chunks; persist question + source_chunks).
Gate 5: Interview loop (submit answer, save feedback stub, return next question).
Gate 6: Summary endpoint (aggregate questions/answers/feedback per session).

# PGAGI MVP Checklist

## Gate 0 — Foundation - DONE [X]
- App boots with `uvicorn app.main:app --reload`
- `GET /api/v1/health` returns 200
- DB init runs and tables are created

## Gate 1 — Resume Intake (stub)  []
- POST /api/v1/resume/upload accepts file
- Parser extracts basic skills/domains
- Resume metadata stored or returned

## Gate 2 — RAG Ingestion  [X]
- Load PDF + txt/md files
- Chunk text (approx 500 tokens, overlap 50-100)
- Embed with sentence-transformers
- Store in ChromaDB with role/source metadata

## Gate 3 — Retrieval   [X]
- Build dynamic query from role + skills
- Retrieve top-k chunks
- Log query + chunks in `retrieval_logs`

- GATE 3.5 : 
Slice by chapter/section and only ingest the chapters that match the role you’re interviewing for.

Remove boilerplate (license pages, table of contents, headers/footers) before chunking.

Store metadata like chapter, page, topic and filter during retrieval (e.g., only topic="backend").

Use smaller chunks (200–350 words) with overlap 40–80 for better precision.

Skip low‑signal pages (pages with very few words or mostly noise).
Prefer curated docs for MVP: 10–30 pages of targeted content beats 300 pages of mixed content.

## Gate 4 — Question Generation   []
- Generate question from chunks
- Store question + source_chunks

## Gate 5 — Interview Loop  []
- Submit answer
- Store feedback stub
- Next question works

## Gate 6 — Summary   []
- GET /api/v1/interview/{id}/summary returns full session data
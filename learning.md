## learnings

- Why settings modeule is important 
A single settings object avoids scattered env lookups 

# Gate 2:  Big picture (kid version)

- We take books (PDF/text), cut them into small pieces, turn each piece into a number list, and store those pieces in a smart drawer (Chroma) so we can find them later.

1) Vector store setup — vector_store.py
Idea: “Create a smart drawer and reuse it every time.”

get_collection() is like “open the same drawer every time” so we don’t make a new one on every request.
PersistentClient makes sure the drawer lives on disk, so it still exists after you stop the app.
get_or_create_collection() makes a named drawer where all chunks go.

2) Embeddings — backend/app/rag/embeddings.py
Idea: “Turn words into numbers so the computer can compare them.”

get_model() loads the embedding model one time and reuses it.
embed_texts() takes text chunks and returns vectors (big lists of numbers).
Those vectors are what Chroma uses for similarity search.

3) Chunking — backend/app/rag/chunking.py
Idea: “Cut a long story into smaller sentences.”

chunk_text() splits a big document into chunks (like small paragraphs).
It uses overlap so pieces share a little context (like pages that repeat a few lines).

4) Ingestion — backend/app/rag/ingest.py
Idea: “Take docs, slice them, turn into numbers, and put into the drawer.”

_load_text() reads PDF/txt/md and returns plain text.
ingest_dir():
scans the docs folder,
reads each file,
chunks it,
embeds it,
stores chunks in Chroma with metadata (role, source, chunk index).
It returns counts so you know it worked.

5) Schemas — schemas.py
Idea: “Rules for what the API should receive and return.”

RagIngestRequest says the API expects a role and optional docs_path.
RagIngestResponse says the API returns how many docs/chunks/vectors were stored.

6) API endpoint — routes.py
Idea: “A button you press to start ingestion.”

POST /api/v1/rag/ingest calls ingest_dir.
It runs in a threadpool so it won’t block the server.
If the folder doesn’t exist, it returns a clean error.

# STATUS / 13-05-2026
- Foundation (Gate 0): Done. App boots, DB models exist, async DB wired, health endpoint works.

- Gate 2 (RAG ingestion): Done. You have loader → chunker → embeddings → Chroma persistence, plus /rag/ingest. You validated with test.txt and got non‑zero counts.

- Current blockers: None. Only note is PDFs without text need OCR.
Next milestone: Gate 3 (retrieval + logging).


# GATE 3: RETrieval
- Request includes session_id, role, skills, context, top_k 
- hybrid query: use query if provided otherwise build a template
- Log to retrieval_logs

# While building prompt for question generation for LM studio :
- I stumbled upon an error which is directly related to the prompt building the mistral model does not support the system prompt and only have user and assitant roles 

- root cause : M Studio’s prompt template for your model doesn’t support the system role.
Your app sends a system + user message, but LM Studio says only user and assistant roles are supported. That’s why you get a 400

# STATUS REPORT (Completed backend end to end pipeline)
Status Report

- JSON hardening for Mistral-compatible chat calls

Kept chat_complete(system, user) signature unchanged, but internally merged both into a single user message (no system role dependency).
llm_client.py:6

Added resilient JSON parser with code-fence cleanup and {...} fallback extraction.
llm_json.py:5

Added schema validation for question and feedback payloads before returning to routes.
question_generator.py:15
answer_evaluator.py:13

Added API-level 502 mapping for invalid LLM payloads (instead of raw 500s).
routes.py:74
routes.py:109

- Role-filtered retrieval

Normalized role at ingest (role.strip().lower()) and stored normalized metadata.
ingest.py:37
Retrieval now accepts optional role and applies Chroma where={"role": ...} filter.
retrieval.py:12
retrieval.py:16
Wired both retrieval endpoints to pass payload.role.
routes.py:62
routes.py:70
Mutable defaults and request validation
Replaced mutable list defaults with Field(default_factory=list).
Added top_k bounds (ge=1, le=20).
schemas.py:41
schemas.py:44
schemas.py:55
schemas.py:57

# Quick recap (14-05-2026) - Easy version

What we just improved:

1) Frontend flow became step-by-step
- Instead of showing everything at once, UI now works like a wizard:
  Start Session -> Upload + Setup -> Question + Answer -> Summary
- This makes the app easier to use and demo.

2) Frontend and backend are now properly connected
- React app is calling your FastAPI endpoints in order.
- Added backend CORS for localhost frontend, so browser calls are allowed.

3) Retrieval quality safety checks added
- Retrieval now supports metadata filtering (role + optional topic/domain).
- We added soft penalties for noisy chunks (example: generic Jupyter/Pandas chunks).
- We rerank chunks and keep better ones first.
- If retrieval confidence is weak, app returns:
  `422 insufficient_context`
  instead of generating a random/low-quality question.

Why this matters:
- Better question relevance
- Fewer weird off-topic questions
- Cleaner user experience
- More production-like behavior for internship review

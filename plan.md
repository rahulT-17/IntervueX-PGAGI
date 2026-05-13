# PGAGI AI/ML & Backend Intern Assignment — Execution Plan

# Core Goal

Build a clean, modular, production-style AI interview system using:
- FastAPI
- PostgreSQL
- RAG pipeline
- React frontend
- Structured orchestration

The goal is NOT to build an overengineered AGI interviewer.

The goal IS to demonstrate:
- backend engineering maturity
- modular architecture
- traceable RAG pipelines
- clean API/system design
- reasoning behind engineering decisions

---

# Guiding Principles

## Prioritize:
- clarity
- modularity
- reliability
- traceability
- maintainability

## Avoid:
- unnecessary agents
- complex memory systems
- overengineering
- excessive abstractions
- fancy UI animations

Think:
> "production-style MVP"

---

# Final System Overview

The system simulates a role-based AI technical interview.

Flow:

Resume Upload
↓
Resume Parsing
↓
Skill Extraction
↓
Role Selection
↓
Dynamic Query Construction
↓
RAG Retrieval
↓
Question Generation
↓
Interview Session
↓
Answer Storage
↓
Summary + Feedback

---

# Recommended Tech Stack

## Backend
- Python
- FastAPI
- SQLAlchemy
- PostgreSQL
- Pydantic
- sentence-transformers
- ChromaDB
- OpenAI-compatible API

## Frontend
- React + Vite
- TailwindCSS (optional)

## Infrastructure
- dotenv
- logging middleware
- Docker (optional)

---

# Project Architecture

backend/
│
├── app/
│   ├── api/
│   │   ├── routes/
│   │   └── dependencies/
│   │
│   ├── core/
│   │   ├── config.py
│   │   ├── security.py
│   │   └── logging.py
│   │
│   ├── db/
│   │   ├── session.py
│   │   └── base.py
│   │
│   ├── models/
│   │
│   ├── schemas/
│   │
│   ├── services/
│   │   ├── resume_parser.py
│   │   ├── retrieval_service.py
│   │   ├── question_generator.py
│   │   ├── interview_service.py
│   │   └── evaluation_service.py
│   │
│   ├── rag/
│   │   ├── ingest.py
│   │   ├── chunking.py
│   │   ├── embeddings.py
│   │   └── vector_store.py
│   │
│   ├── utils/
│   │
│   └── main.py
│
├── requirements.txt
├── README.md
└── .env.example

---

# Frontend Structure

frontend/
│
├── src/
│   ├── pages/
│   │   ├── UploadPage.jsx
│   │   ├── InterviewPage.jsx
│   │   └── SummaryPage.jsx
│   │
│   ├── components/
│   │
│   ├── services/
│   │
│   └── App.jsx

Keep frontend minimal and functional.

---

# Core System Components

# 1. Resume Upload + Parsing

## Goal
Extract:
- skills
- technologies
- domains
- experience indicators

## Implementation
Use:
- pdfplumber or PyMuPDF
- lightweight extraction logic

Avoid:
- heavy NLP pipelines

## Output Example

{
  "skills": ["Python", "FastAPI", "PostgreSQL"],
  "domains": ["Backend Engineering", "AI Systems"],
  "experience_level": "Intermediate"
}

---

# 2. Knowledge Base Ingestion

## Goal
Build a role-specific RAG knowledge base.

## Steps
1. Load PDFs/books
2. Chunk text
3. Generate embeddings
4. Store in vector DB

## Recommended
- Recursive chunking
- Chunk size: ~500 tokens
- Overlap: 50–100

## Store
{
  "chunk",
  "source",
  "role_type",
  "embedding"
}

---

# 3. Retrieval Pipeline

## MOST IMPORTANT COMPONENT

Dynamic retrieval based on:
- selected role
- extracted resume skills
- interview context

## Example Query

"Intermediate backend engineering interview topics for FastAPI and PostgreSQL"

NOT:
"machine learning"

## Goal
Relevant retrieval.
Not generic retrieval.

---

# 4. Question Generation

Input:
- retrieved chunks
- role
- resume skills
- previous context

Output:
{
  "question",
  "topic",
  "difficulty",
  "source_chunks"
}

## Important
Questions should:
- feel contextual
- reference candidate background
- avoid generic outputs

---

# 5. Interview Session Engine

Maintain:
- session state
- question history
- answers
- timestamps

## Responsibilities
- generate next question
- store interactions
- maintain continuity

Keep logic simple and traceable.

---

# 6. Answer Evaluation

DO NOT build fake AGI evaluation.

Keep simple:
- summarize answer
- compare with retrieved context
- generate lightweight feedback

Example:
- strengths
- missing concepts
- confidence estimate

Enough for assignment quality.

---

# Database Design

# Tables

## users
- id
- name
- created_at

## interview_sessions
- id
- user_id
- role
- created_at

## questions
- id
- session_id
- question
- topic
- difficulty
- source_chunks

## answers
- id
- question_id
- answer
- generated_feedback

## retrieval_logs
(HIGH SIGNAL TABLE)

- id
- session_id
- generated_query
- retrieved_chunks
- timestamps

This demonstrates:
- observability
- traceability
- pipeline visibility

---

# API Design

# Main Endpoints

## Resume
POST /api/v1/resume/upload

## Start Interview
POST /api/v1/interview/start

## Generate Question
POST /api/v1/interview/question

## Submit Answer
POST /api/v1/interview/answer

## Summary
GET /api/v1/interview/{id}/summary

---

# Frontend Plan

# Upload Page
- upload resume
- select role
- start interview

# Interview Page
- display question
- answer input
- submit answer
- next question

# Summary Page
- show questions
- show answers
- feedback summary

Keep:
- clean
- minimal
- functional

DO NOT overbuild UI.

---

# Traceability Layer (Differentiator)

This is the strongest engineering signal.

For every question:
Store:
- generated query
- retrieved chunks
- generated question
- answer
- timestamps

This turns:
> "chatbot"

into:
> "traceable AI pipeline"

---

# Observability

Add lightweight logging:
- request logs
- retrieval logs
- latency logs

Optional:
simple dashboard metrics.

Do NOT overengineer monitoring.

---

# README Strategy

README matters heavily.

Include:
- architecture diagram
- system flow
- tech stack
- setup instructions
- API examples
- retrieval strategy
- chunking decisions
- design tradeoffs
- scaling ideas

---

# Demo Video Strategy

Focus on:
1. Resume upload
2. Role selection
3. Retrieval + question generation
4. Interview flow
5. Stored answers
6. Summary output
7. Explain architecture briefly

Keep concise:
5–8 mins.

---

# What NOT To Build

Do NOT add:
- multi-agent systems
- autonomous evaluators
- advanced memory architectures
- complex recommendation systems
- unnecessary microservices
- websocket complexity
- fancy animations

This is an intern assignment.
Clean engineering wins.

---

# What Will Actually Impress Reviewers

## Highest Signal
- modular backend
- clean API flow
- structured RAG pipeline
- traceability
- observability
- database design
- retrieval reasoning
- clean README

## NOT Highest Signal
- flashy frontend
- AI buzzwords
- overcomplicated prompts

---

# Time Allocation Plan

# Phase 1 — Backend Foundation
- FastAPI setup
- DB models
- session management
- APIs

# Phase 2 — RAG Pipeline
- ingestion
- embeddings
- retrieval
- vector DB

# Phase 3 — Question Generation
- prompt pipeline
- contextual questions
- answer storage

# Phase 4 — Frontend
- upload page
- interview flow
- summary page

# Phase 5 — Polish
- README
- logging
- cleanup
- demo video

---

# Final Philosophy

The winning submission is NOT:
> "most complex"

It is:
> "most production-minded"

Your edge is:
- systems thinking
- orchestration mindset
- backend architecture intuition
- observability awareness

Lean into that.
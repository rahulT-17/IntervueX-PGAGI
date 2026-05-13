from fastapi import APIRouter, Depends, HTTPException
from fastapi.concurrency import run_in_threadpool

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import get_db  # replace with your actual import
from app.models import User, InterviewSession  # replace with your actual import
from app.schemas import InterviewStartRequest, InterviewStartResponse, RagIngestRequest, RagIngestResponse, RagRetrieveRequest, RagRetrieveResponse

from app.rag.ingest import ingest_dir
from app.rag.retrieval import build_query, retrieve_chunks
from app.services.retrieval_logger import log_retrieval

router = APIRouter(prefix="/api/v1")

@router.get("/health")
async def health():
    return {"status": "backend is healthy"}

@router.post("/interview/start", response_model=InterviewStartResponse)
async def start_interview(payload: InterviewStartRequest, db: AsyncSession = Depends(get_db)):
    user = User(name=payload.user_name)
    db.add(user)
    await db.flush()  # get user.id without commit

    session = InterviewSession(user_id=user.id, role=payload.role)
    db.add(session)
    await db.commit()
    await db.refresh(session)

    return InterviewStartResponse(session_id=session.id)

@router.post("/rag/ingest", response_model=RagIngestResponse)
async def ingest_rag_docs(payload: RagIngestRequest):
    try:
        result = await run_in_threadpool(ingest_dir, payload.role, payload.docs_path)

    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    
    return result

@router.post("/rag/retrieve", response_model=RagRetrieveResponse)
async def retrieve_rag(payload: RagRetrieveRequest, db: AsyncSession = Depends(get_db)):
    
    query = payload.query or build_query(payload.role, payload.skills, payload.context)
    chunks = retrieve_chunks(query, payload.top_k)

    await log_retrieval(db, payload.session_id, query, chunks)
    return RagRetrieveResponse(query=query, top_k=payload.top_k, chunks=chunks)
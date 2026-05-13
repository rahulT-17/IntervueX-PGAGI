from fastapi import APIRouter, Depends, HTTPException
from fastapi.concurrency import run_in_threadpool

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import get_db 
from app.models import User, InterviewSession, Question, Answer
from app.schemas import (
    InterviewStartRequest, 
    InterviewStartResponse,
    RagIngestRequest, 
    RagIngestResponse, 
    RagRetrieveRequest, 
    RagRetrieveResponse,
    InterviewQuestionRequest, 
    InterviewQuestionResponse,
    AnswerSubmitRequest,
    AnswerSubmitResponse,
    )

from app.rag.ingest import ingest_dir
from app.rag.retrieval import build_query, retrieve_chunks
from app.services.retrieval_logger import log_retrieval
from app.services.question_generator import generate_question
from app.services.answer_evaluator import evaluate_answer


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

@router.post("/interview/question", response_model=InterviewQuestionResponse)
async def generate_interview_question(payload: InterviewQuestionRequest, db: AsyncSession = Depends(get_db)):
    query = payload.query or build_query(payload.role, payload.skills, payload.context)
    chunks = retrieve_chunks(query, payload.top_k)

    result = await generate_question(payload.role, payload.skills, payload.context, chunks)
    question = Question(
        session_id=payload.session_id,
        question=result["question"],
        topic=result["topic"],
        difficulty=result["difficulty"],
        source_chunks=chunks,
    )

    db.add(question)
    await db.commit()
    await db.refresh(question)

    return InterviewQuestionResponse(
        question_id=question.id,
        question=question.question,
        topic=question.topic,
        difficulty=question.difficulty,
        source_chunks=question.source_chunks,
    )

@router.post("/interview/answer", response_model=AnswerSubmitResponse)
async def submit_answer(payload: AnswerSubmitRequest, db: AsyncSession = Depends(get_db)):
    question = await db.get(Question, payload.question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    feedback = await evaluate_answer(
        question.question,
        payload.answer,
        question.source_chunks,
    )

    answer = Answer(
        question_id=payload.question_id,
        answer=payload.answer,
        generated_feedback=feedback,
    )
    db.add(answer)
    await db.commit()
    await db.refresh(answer)

    return AnswerSubmitResponse(
        answer_id=answer.id,
        generated_feedback=answer.generated_feedback,
    )
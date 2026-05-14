from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.concurrency import run_in_threadpool
from pydantic import ValidationError

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import get_db 
from app.models import User, InterviewSession, Question, Answer, RetrievalLog, Resume
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
    InterviewSummaryResponse,
    SummaryQuestion,
    SummaryAnswer,
    SummaryRetrievalLog,
    ResumeUploadResponse,
    ResumeGetResponse,

    )

from app.rag.ingest import ingest_dir
from app.rag.retrieval import build_query, retrieve_chunks

from app.services.retrieval_logger import log_retrieval
from app.services.question_generator import generate_question
from app.services.answer_evaluator import evaluate_answer
from app.services.resume_parser import extract_resume_text, parse_resume



router = APIRouter(prefix="/api/v1")

def _resume_role_and_skills(resume: Resume | None) -> tuple[str | None, list[str]]:
    if not resume or not isinstance(resume.parsed_profile, dict):
        return None, []

    profile = resume.parsed_profile
    roles = profile.get("target_roles") or []
    skills = profile.get("skills") or []

    role = None
    if isinstance(roles, list) and roles:
        role = str(roles[0]).strip().lower()

    clean_skills = []
    if isinstance(skills, list):
        clean_skills = [str(s).strip() for s in skills if str(s).strip()]

    return role, clean_skills


async def _load_resume_for_session(db: AsyncSession, resume_id: int, session_id: int) -> Resume:
    resume = await db.get(Resume, resume_id)
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    if resume.session_id is not None and resume.session_id != session_id:
        raise HTTPException(status_code=400, detail="Resume does not belong to this session")

    return resume

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
    session = await db.get(InterviewSession, payload.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    resume = None
    if payload.resume_id is not None:
        resume = await _load_resume_for_session(db, payload.resume_id, payload.session_id)

    resume_role, resume_skills = _resume_role_and_skills(resume)

    resolved_role = (payload.role or resume_role or session.role or "backend").strip().lower()
    resolved_skills = payload.skills if payload.skills else resume_skills

    query = payload.query or build_query(resolved_role, resolved_skills, payload.context)
    chunks = retrieve_chunks(query, payload.top_k, role=resolved_role)

    await log_retrieval(db, payload.session_id, query, chunks)
    return RagRetrieveResponse(query=query, top_k=payload.top_k, chunks=chunks)


@router.post("/interview/question", response_model=InterviewQuestionResponse)
async def generate_interview_question(payload: InterviewQuestionRequest, db: AsyncSession = Depends(get_db)):
    session = await db.get(InterviewSession, payload.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    resume = None
    if payload.resume_id is not None:
        resume = await _load_resume_for_session(db, payload.resume_id, payload.session_id)

    resume_role, resume_skills = _resume_role_and_skills(resume)

    resolved_role = (payload.role or resume_role or session.role or "backend").strip().lower()
    resolved_skills = payload.skills if payload.skills else resume_skills

    query = payload.query or build_query(resolved_role, resolved_skills, payload.context)
    chunks = retrieve_chunks(query, payload.top_k, role=resolved_role)

    try:
        result = await generate_question(resolved_role, resolved_skills, payload.context, chunks)
    except (ValueError, ValidationError) as exc:
        raise HTTPException(status_code=502, detail=f"Invalid LLM question payload: {exc}") from exc
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Question generation failed. Check LLM_BASE_URL/model server. Error: {exc}",
        ) from exc

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

    try:
        feedback = await evaluate_answer(
            question.question,
            payload.answer,
            question.source_chunks,
        )
    except (ValueError, ValidationError) as exc:
        raise HTTPException(status_code=502, detail=f"Invalid LLM feedback payload: {exc}") from exc
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Answer evaluation failed. Check LLM_BASE_URL/model server. Error: {exc}",
        ) from exc

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


@router.get("/interview/{session_id}/summary", response_model=InterviewSummaryResponse)
async def get_summary(session_id: int, include_chunks: bool = False, db: AsyncSession = Depends(get_db)):
    session = await db.get(InterviewSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    q_result = await db.execute(
        select(Question).where(Question.session_id == session_id)
    )
    questions = q_result.scalars().all()
    question_ids = [q.id for q in questions]

    answers_map: dict[int, list[Answer]] = {}
    if question_ids:
        a_result = await db.execute(
            select(Answer).where(Answer.question_id.in_(question_ids))
        )
        for ans in a_result.scalars().all():
            answers_map.setdefault(ans.question_id, []).append(ans)

    r_result = await db.execute(
        select(RetrievalLog)
        .where(RetrievalLog.session_id == session_id)
        .order_by(RetrievalLog.created_at)
    )
    logs = r_result.scalars().all()

    summary_questions: list[SummaryQuestion] = []
    for q in questions:
        summary_questions.append(
            SummaryQuestion(
                id=q.id,
                question=q.question,
                topic=q.topic,
                difficulty=q.difficulty,
                source_chunks=q.source_chunks if include_chunks else [],
                answers=[
                    SummaryAnswer(
                        id=a.id,
                        answer=a.answer,
                        generated_feedback=a.generated_feedback,
                    )
                    for a in answers_map.get(q.id, [])
                ],
            )
        )

    return InterviewSummaryResponse(
        session_id=session.id,
        role=session.role,
        questions=summary_questions,
        retrieval_logs=[
            SummaryRetrievalLog(
                id=log.id,
                generated_query=log.generated_query,
                retrieved_chunks=log.retrieved_chunks if include_chunks else [],
                created_at=log.created_at,
            )
            for log in logs
        ],
    )

@router.post("/resume/upload", response_model=ResumeUploadResponse)
async def upload_resume(
    file: UploadFile = File(...),
    session_id: int | None = Form(None),
    target_role: str | None = Form(None),
    db: AsyncSession = Depends(get_db),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")

    if session_id is not None:
        session = await db.get(InterviewSession, session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    try:
        raw_text = await run_in_threadpool(extract_resume_text, file.filename, content)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if not raw_text.strip():
        raise HTTPException(status_code=400, detail="Could not extract text from resume")

    parsed_profile, confidence, missing_fields = await run_in_threadpool(
        parse_resume, raw_text, target_role
    )

    resume = Resume(
        session_id=session_id,
        filename=file.filename,
        raw_text=raw_text,
        parsed_profile=parsed_profile,
        confidence=confidence,
        missing_fields=missing_fields,
    )
    db.add(resume)
    await db.commit()
    await db.refresh(resume)

    return ResumeUploadResponse(
        resume_id=resume.id,
        session_id=resume.session_id,
        filename=resume.filename,
        raw_text_preview=resume.raw_text[:600],
        parsed_profile=resume.parsed_profile,
        confidence=resume.confidence,
        missing_fields=resume.missing_fields,
    )


@router.get("/resume/{resume_id}", response_model=ResumeGetResponse)
async def get_resume(resume_id: int, db: AsyncSession = Depends(get_db)):
    resume = await db.get(Resume, resume_id)
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    return ResumeGetResponse(
        resume_id=resume.id,
        session_id=resume.session_id,
        filename=resume.filename,
        parsed_profile=resume.parsed_profile,
        confidence=resume.confidence,
        missing_fields=resume.missing_fields,
    )

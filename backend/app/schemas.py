from pydantic import BaseModel
from datetime import datetime

class InterviewStartRequest(BaseModel):
    user_name: str
    role: str

class InterviewStartResponse(BaseModel):
    session_id: int

class QuestionRequest(BaseModel):
    session_id: int

class QuestionResponse(BaseModel):
    question_id: int
    question: str
    topic: str
    difficulty: str
    source_chunks: list[dict]

class AnswerRequest(BaseModel):
    question_id: int
    answer: str

class AnswerResponse(BaseModel):
    answer_id: int
    generated_feedback: str

class RagIngestRequest(BaseModel):
    role: str
    docs_path: str | None = None


class RagIngestResponse(BaseModel):
    documents: int
    chunks: int
    vectors: int

class RagRetrieveRequest(BaseModel):
    session_id: int
    role: str
    skills: list[str] = []
    context: str | None = None
    query: str | None = None
    top_k: int = 6


class RagRetrieveResponse(BaseModel):
    query: str
    top_k: int
    chunks: list[dict]

class InterviewQuestionRequest(BaseModel):
    session_id: int
    role: str
    skills: list[str] = []
    context: str | None = None
    top_k: int = 6
    query: str | None = None


class InterviewQuestionResponse(BaseModel):
    question_id: int
    question: str
    topic: str
    difficulty: str
    source_chunks: list[dict]

class AnswerSubmitRequest(BaseModel):
    question_id: int
    answer: str


class AnswerSubmitResponse(BaseModel):
    answer_id: int
    generated_feedback: dict

class SummaryAnswer(BaseModel):
    id: int
    answer: str
    generated_feedback: dict

class SummaryQuestion(BaseModel):
    id: int
    question: str
    topic: str
    difficulty: str
    source_chunks: list[dict]
    answers: list[SummaryAnswer]

class SummaryRetrievalLog(BaseModel):
    id: int
    generated_query: str
    retrieved_chunks: list[dict]
    created_at: datetime

class InterviewSummaryResponse(BaseModel):
    session_id: int
    role: str
    questions: list[SummaryQuestion]
    retrieval_logs: list[SummaryRetrievalLog]
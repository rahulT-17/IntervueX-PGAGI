from datetime import datetime

from pydantic import BaseModel, Field

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
    role: str | None = None
    skills: list[str] = Field(default_factory=list)
    context: str | None = None
    query: str | None = None
    top_k: int = Field(default=6, ge=1, le=20)
    resume_id: int | None = None

class RagRetrieveResponse(BaseModel):
    query: str
    top_k: int
    chunks: list[dict]

class InterviewQuestionRequest(BaseModel):
    session_id: int
    role: str | None = None
    skills: list[str] = Field(default_factory=list)
    context: str | None = None
    top_k: int = Field(default=6, ge=1, le=20)
    query: str | None = None
    resume_id: int | None = None

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


class ResumeParsedProfile(BaseModel):
    full_name: str | None = None
    email: str | None = None
    phone: str | None = None
    years_experience: int | None = None
    skills: list[str] = Field(default_factory=list)
    target_roles: list[str] = Field(default_factory=list)
    links: list[str] = Field(default_factory=list)


class ResumeUploadResponse(BaseModel):
    resume_id: int
    session_id: int | None
    filename: str
    raw_text_preview: str
    parsed_profile: ResumeParsedProfile
    confidence: dict
    missing_fields: list[str]


class ResumeGetResponse(BaseModel):
    resume_id: int
    session_id: int | None
    filename: str
    parsed_profile: ResumeParsedProfile
    confidence: dict
    missing_fields: list[str]

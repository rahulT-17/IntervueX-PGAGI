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
    role: str
    skills: list[str] = Field(default_factory=list)
    context: str | None = None
    query: str | None = None
    top_k: int = Field(default=6, ge=1, le=20)


class RagRetrieveResponse(BaseModel):
    query: str
    top_k: int
    chunks: list[dict]

class InterviewQuestionRequest(BaseModel):
    session_id: int
    role: str
    skills: list[str] = Field(default_factory=list)
    context: str | None = None
    top_k: int = Field(default=6, ge=1, le=20)
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

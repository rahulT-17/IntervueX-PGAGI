from pydantic import BaseModel

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
    generated_feedback: dict
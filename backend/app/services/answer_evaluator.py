from pydantic import BaseModel

from app.services.llm_client import chat_complete
from app.services.llm_json import parse_json_object


SYSTEM_PROMPT = """You are a technical interview evaluator.
Return JSON only with keys: strengths, missing_concepts, overall_feedback.
strengths and missing_concepts must be arrays of short strings.
"""


class FeedbackPayload(BaseModel):
    strengths: list[str]
    missing_concepts: list[str]
    overall_feedback: str


def _build_prompt(question: str, answer: str, source_chunks: list[dict]) -> str:
    chunk_text = "\n\n".join([f"- {c['content'][:600]}" for c in source_chunks[:3]])
    return f"""
Question:
{question}

Candidate Answer:
{answer}

Reference Context:
{chunk_text}

Evaluate the answer based on the reference context.
"""


async def evaluate_answer(question: str, answer: str, source_chunks: list[dict]) -> dict:
    prompt = _build_prompt(question, answer, source_chunks)
    raw = await chat_complete(SYSTEM_PROMPT, prompt)
    payload = parse_json_object(raw)
    return FeedbackPayload.model_validate(payload).model_dump()

from typing import Literal

from pydantic import BaseModel

from app.services.llm_client import chat_complete
from app.services.llm_json import parse_json_object


SYSTEM_PROMPT = """You are an interview question generator.
Return JSON only with keys: question, topic, difficulty.
Difficulty must be one of: easy, medium, hard.
"""


class QuestionPayload(BaseModel):
    question: str
    topic: str
    difficulty: Literal["easy", "medium", "hard"]


def _build_prompt(role: str, skills: list[str], context: str | None, chunks: list[dict]) -> str:
    skills_str = ", ".join(skills) if skills else "general backend topics"
    context_str = context or "N/A"
    chunk_text = "\n\n".join([f"- {c['content'][:800]}" for c in chunks[:4]])
    return f"""
Role: {role}
Skills: {skills_str}
Context: {context_str}

Retrieved context:
{chunk_text}

Generate one interview question grounded in the retrieved context.
"""


async def generate_question(role: str, skills: list[str], context: str | None, chunks: list[dict]) -> dict:
    prompt = _build_prompt(role, skills, context, chunks)
    raw = await chat_complete(SYSTEM_PROMPT, prompt)
    payload = parse_json_object(raw)
    return QuestionPayload.model_validate(payload).model_dump()

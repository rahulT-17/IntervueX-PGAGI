import json

from app.services.llm_client import chat_complete


SYSTEM_PROMPT = """You are a technical interview evaluator.
Return JSON only with keys: strengths, missing_concepts, overall_feedback.
strengths and missing_concepts must be arrays of short strings.
"""


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
    return json.loads(raw)
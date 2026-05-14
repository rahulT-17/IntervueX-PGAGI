from __future__ import annotations

from app.rag.vector_store import get_collection

PENALTY_TERMS = [
    "jupyter notebook launch",
    "pandas install",
    "notebook viewer",
]

MIN_RETRIEVAL_CONFIDENCE = 0.45

SKILL_EXPANSION = {
    "fastapi": ["asgi", "python web api", "dependency injection", "pydantic"],
    "sqlalchemy": ["orm", "session management", "async session"],
    "postgresql": ["postgres", "query optimization", "indexing", "transactions"],
    "docker": ["containerization", "image", "runtime"],
    "rag": ["retrieval augmented generation", "vector database", "embeddings"],
    "llm": ["large language model", "prompting", "inference"],
    "langchain": ["chains", "retriever", "tool calling"]
}

def expand_skills(skills: list[str]) -> list[str]:
    out = []
    for s in skills:
        k = s.strip().lower()
        out.append(k)
        out.extend(SKILL_EXPANSION.get(k, []))
    return list(dict.fromkeys(out))


def build_query(role: str, skills: list[str], context: str | None = None) -> str:
    expanded = expand_skills(skills)
    skills_str = ", ".join(expanded) if expanded else "general backend topics"
    ctx = f" Context: {context}." if context else ""
    return f"{role} interview topics for {skills_str}.{ctx}"


def retrieve_chunks(query: str, top_k: int = 6, role: str | None = None, topic: str | None = None, domain: str | None = None) -> list[dict]:
    collection = get_collection()
    query_kwargs = {"query_texts": [query], "n_results": top_k}
    where: dict[str, str] = {}
    if role:
        where["role"] = role.strip().lower()
    if topic:
        where["topic"] = topic.strip().lower()
    if domain:
        where["domain"] = domain.strip().lower()
    if where:
        query_kwargs["where"] = where

    result = collection.query(**query_kwargs)
    chunks: list[dict] = []

    for idx in range(len(result["documents"][0])):
        chunks.append(
            {
                "content": result["documents"][0][idx],
                "metadata": result["metadatas"][0][idx],
                "score": result["distances"][0][idx] if result.get("distances") else None,
            }
        )

    ranked = sorted(chunks, key=lambda c: score_chunk(c, query), reverse=True)
    selected = ranked[: min(4, len(ranked))]
    if not selected:
        return []

    mean_score = sum(score_chunk(c, query) for c in selected) / len(selected)
    if mean_score < MIN_RETRIEVAL_CONFIDENCE:
        return []

    return selected


def score_chunk(chunk: dict, query: str) -> float:
    base = 1.0
    text = (chunk.get("content") or "").lower()
    q = query.lower()

    for token in q.split():
        if len(token) > 3 and token in text:
            base += 0.03

    for penalty in PENALTY_TERMS:
        if penalty in text:
            base -= 0.2

    distance = chunk.get("score")
    if isinstance(distance, (float, int)):
        base -= min(float(distance), 1.0) * 0.4

    return base

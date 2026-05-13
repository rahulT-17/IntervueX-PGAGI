from __future__ import annotations

from app.rag.vector_store import get_collection


def build_query(role: str, skills: list[str], context: str | None = None) -> str:
    skills_str = ", ".join(skills) if skills else "general backend topics"
    ctx = f" Context: {context}." if context else ""
    return f"{role} interview topics for {skills_str}.{ctx}"


def retrieve_chunks(query: str, top_k: int = 6) -> list[dict]:
    collection = get_collection()
    result = collection.query(query_texts=[query], n_results=top_k)
    chunks: list[dict] = []

    for idx in range(len(result["documents"][0])):
        chunks.append(
            {
                "content": result["documents"][0][idx],
                "metadata": result["metadatas"][0][idx],
                "score": result["distances"][0][idx] if result.get("distances") else None,
            }
        )

    return chunks
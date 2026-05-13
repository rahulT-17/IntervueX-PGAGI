from __future__ import annotations

import hashlib
from pathlib import Path

import pdfplumber

from app.core.settings import settings
from app.rag.chunking import chunk_text
from app.rag.embeddings import embed_texts
from app.rag.vector_store import get_collection

SUPPORTED_EXTS = {".pdf", ".txt", ".md"}


def _load_text(path: Path) -> str:
    if path.suffix.lower() in {".txt", ".md"}:
        return path.read_text(encoding="utf-8", errors="ignore")
    if path.suffix.lower() == ".pdf":
        pages: list[str] = []
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                pages.append(page.extract_text() or "")
        return "\n".join(pages)
    return ""


def ingest_dir(role: str, docs_path: str | None = None) -> dict:
    docs_dir = Path(docs_path) if docs_path else Path(settings.rag_docs_dir)
    if not docs_dir.exists():
        raise FileNotFoundError(f"Docs directory not found: {docs_dir}")

    docs: list[tuple[Path, str]] = []
    for path in docs_dir.rglob("*"):
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTS:
            text = _load_text(path).strip()
            if text:
                docs.append((path, text))

    ids: list[str] = []
    documents: list[str] = []
    metadatas: list[dict] = []

    for path, text in docs:
        doc_id = hashlib.sha256(str(path).encode("utf-8")).hexdigest()[:16]
        chunks = chunk_text(text)
        for i, chunk in enumerate(chunks):
            ids.append(f"{doc_id}_{i}")
            documents.append(chunk)
            metadatas.append(
                {
                    "role": role,
                    "source": str(path),
                    "chunk_index": i,
                }
            )

    if documents:
        vectors = embed_texts(documents)
        collection = get_collection()
        collection.upsert(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
            embeddings=vectors,
        )

    return {
        "documents": len(docs),
        "chunks": len(documents),
        "vectors": len(documents),
    }
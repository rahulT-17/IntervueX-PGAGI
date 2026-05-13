from __future__ import annotations

import re
import hashlib
from pathlib import Path

import fitz # PyMuPDF

from app.core.settings import settings
from app.rag.chunking import chunk_text
from app.rag.embeddings import embed_texts
from app.rag.vector_store import get_collection

SUPPORTED_EXTS = {".pdf", ".txt", ".md"}


def _clean_text(text: str) -> str:
    text = text.replace("\n", " ")
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"(?<=\w)-\s+(?=\w)", "", text)  # fix hyphen line breaks
    return text.strip()

def _load_text(path: Path) -> str:
    if path.suffix.lower() in {".txt", ".md"}:
        return _clean_text(path.read_text(encoding="utf-8", errors="ignore"))
    
    if path.suffix.lower() == ".pdf":
        pages: list[str] = []
        with fitz.open(path) as doc:
            for page in doc:
                pages.append(_clean_text(page.get_text("text") or ""))
        return _clean_text(" ".join(pages))
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


from functools import lru_cache

import chromadb
from chromadb.api.models.Collection import Collection

from app.core.settings import settings


@lru_cache(maxsize=1)
def get_collection() -> Collection:
    client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
    return client.get_or_create_collection(
        name=settings.chroma_collection_name,
        metadata={"hnsw:space": "cosine"},
    )
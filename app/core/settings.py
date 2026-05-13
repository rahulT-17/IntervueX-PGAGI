from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=True,
        extra="ignore",
    )

    env: str = "dev"
    database_url: str
    log_level: str = "INFO"
    rag_docs_dir: str = "data/docs"
    chroma_persist_dir: str = "data/chroma"
    chroma_collection_name: str = "pgagi_rag"
    embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    chunk_size: int = 80
    chunk_overlap: int = 20

settings = Settings()
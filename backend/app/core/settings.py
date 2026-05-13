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
    chunk_size: int = 500
    chunk_overlap: int = 80
    llm_base_url: str = "http://127.0.0.1:1234/v1"
    llm_api_key: str = "local"
    llm_model: str = "mistralai/mistral-7b-instruct-v0.3"

settings = Settings()
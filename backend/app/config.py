
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # PostgreSQL
    database_url: str = ""

    # Gemini LLM
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"

    # Local embeddings
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"

    # Repository storage
    data_dir: str = "./data"
    repo_dir: str = "./repos"
    max_files: int = 2500
    max_file_bytes: int = 300_000
    chunk_lines: int = 80
    chunk_overlap: int = 12

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()

Path(settings.data_dir).mkdir(parents=True, exist_ok=True)
Path(settings.repo_dir).mkdir(parents=True, exist_ok=True)

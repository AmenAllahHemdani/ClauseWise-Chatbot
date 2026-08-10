from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    google_api_key: str = ""
    llm_model: str = "gemini-2.5-flash"

    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "clausewise_chunks"
    embedding_model: str = "BAAI/bge-small-en-v1.5"

    mongo_url: str = ""
    mongo_db: str = "clausewise"

    mode: str = "dev"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    max_upload_mb: int = 25

    upload_dir: Path = PROJECT_ROOT / "data" / "uploads"


settings = Settings()

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import PostgresDsn

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application
    APP_NAME: str = "Gopedia Headless Engine"
    DEBUG: bool = False

    # Database (PostgreSQL + pgvector)
    DATABASE_URL: PostgresDsn

    # gRPC Plugin Registry (Simple mapping for MVP)
    # e.g., {"jira": "localhost:50051", "ai_summarizer": "ai-svc:50052"}
    PLUGIN_REGISTRY: dict[str, str] = {}

settings = Settings()
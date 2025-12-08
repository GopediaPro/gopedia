from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import PostgresDsn, Field
from typing import Optional

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Database
    DATABASE_URL: PostgresDsn = Field(..., description="PostgreSQL Connection URL")
    
    # Application
    APP_ENV: str = Field("development", description="Environment: development, production, testing")
    LOG_LEVEL: str = Field("INFO", description="Logging level")

    # gRPC Plugin Defaults
    DEFAULT_PLUGIN_TIMEOUT: int = Field(5, description="Default timeout for plugin calls in seconds")
    
    # GitHub API Settings
    GITHUB_OWNER: Optional[str] = Field(None, description="GitHub repository owner (default for seeding)")
    GITHUB_REPO: Optional[str] = Field(None, description="GitHub repository name (default for seeding)")
    GITHUB_BRANCH: str = Field("main", description="GitHub branch name (default: main)")
    GITHUB_TOKEN: Optional[str] = Field(None, description="GitHub personal access token (optional, for rate limits)")

    # LLM / Embedding
    LLM_API_KEY: Optional[str] = Field(None, description="API key for LLM/embedding provider")
    LLM_MODEL: str = Field("text-embedding-3-small", description="Default LLM/embedding model name")

settings = Settings()

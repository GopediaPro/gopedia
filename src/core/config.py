from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import PostgresDsn, Field

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Database
    DATABASE_URL: PostgresDsn = Field(..., description="PostgreSQL Connection URL")
    
    # Application
    APP_ENV: str = Field("development", description="Environment: development, production, testing")
    LOG_LEVEL: str = Field("INFO", description="Logging level")

    # gRPC Plugin Defaults
    DEFAULT_PLUGIN_TIMEOUT: int = Field(5, description="Default timeout for plugin calls in seconds")

settings = Settings()

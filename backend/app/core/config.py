import os
from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "BusinessPulse AI"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = os.getenv("JWT_SECRET", "super-secret-businesspulse-dev-key-change-in-prod-32chars")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALGORITHM: str = "HS256"

    # Multi-tenant and Database settings
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/bizpulse"
    )
    # SQLite fallback for quick local testing when PostgreSQL is unavailable
    SQLITE_FALLBACK_URL: str = "sqlite:///./bizpulse_test.db"
    USE_SQLITE_FALLBACK: bool = os.getenv("USE_SQLITE_FALLBACK", "false").lower() in ("true", "1", "t")

    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8000",
        "http://127.0.0.1:5173",
    ]

    # File uploads and artifacts
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "./data/uploads")
    MODEL_ARTIFACTS_DIR: str = os.getenv("MODEL_ARTIFACTS_DIR", "./ml/artifacts")

    # OpenAI / AI Explainer
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()


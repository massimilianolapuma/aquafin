"""Application settings loaded from environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration with env-var support."""

    # App
    APP_NAME: str = "Aquafin"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://aquafin:aquafin@localhost:5432/aquafin"

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    # Auth (Clerk)
    CLERK_SECRET_KEY: str = ""
    CLERK_PUBLISHABLE_KEY: str = ""

    # File upload
    UPLOAD_MAX_SIZE_MB: int = 10
    UPLOAD_TEMP_DIR: str = "/tmp/aquafin-uploads"
    UPLOAD_RETENTION_HOURS: int = 24

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }


settings = Settings()

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Database
    DATABASE_URL: str = "sqlite:///./appointments.db"

    # Application
    APP_ENV: str = "development"  # development, production, test
    APP_NAME: str = "Healthcare Appointment API"
    APP_VERSION: str = "1.0.0"

    # Timezone
    TIMEZONE: str = "America/Toronto"

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Global settings instance
settings = Settings()

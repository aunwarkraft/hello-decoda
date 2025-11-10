from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from typing import Union
import json


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        env_ignore_empty=True,
    )

    # Database
    DATABASE_URL: str = "sqlite:///./appointments.db"

    # Application
    APP_ENV: str = "development"  # development, production, test
    APP_NAME: str = "Healthcare Appointment API"
    APP_VERSION: str = "1.0.0"

    # Timezone
    TIMEZONE: str = "America/Toronto"

    # CORS - can be JSON string or comma-separated string
    CORS_ORIGINS: Union[str, list[str]] = ["http://localhost:3000"]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS_ORIGINS from JSON string or comma-separated string"""
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            # Try to parse as JSON first
            try:
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return parsed
            except (json.JSONDecodeError, TypeError):
                pass
            # If not JSON, try comma-separated string
            origins = [origin.strip() for origin in v.split(",") if origin.strip()]
            return origins if origins else ["http://localhost:3000"]
        return ["http://localhost:3000"]


# Global settings instance
settings = Settings()

"""
Centralized configuration management for the application.

This module provides a single source of truth for all environment variables
and configuration settings used throughout the application.
"""

from typing import Optional
from pydantic import Field, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable fallbacks."""

    # N8N Configuration
    N8N_BASE_URL: Optional[str] = Field(
        default=None,
        description="Base URL for n8n instance (optional, overrides webhook base URL if set)",
    )
    N8N_WEBHOOK_BASE_URL: str = Field(
        ...,
        description="Base URL for n8n webhooks (e.g., 'https://your-n8n-instance.com')",
    )
    N8N_API_KEY: Optional[str] = Field(
        default=None, description="API key for n8n authentication"
    )
    N8N_ENV: str = Field(
        default="development",
        description="Environment (development, test, staging, production)",
    )

    # LLM Configuration
    CLAUDE_API_KEY: str = Field(..., description="Claude API key for LLM access")
    CLAUDE_MODEL: str = Field(
        ..., description="Claude model name (e.g., 'claude-3-opus-20240229')"
    )

    # Logging Configuration
    LOG_LEVEL: str = Field(
        "INFO", description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    )

    @validator("N8N_ENV")
    def validate_environment(cls, v):
        """Ensure environment is one of the allowed values."""
        allowed = {"test", "development", "staging", "production"}
        if v not in allowed:
            raise ValueError(f"N8N_ENV must be one of {allowed}")
        return v

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
        "extra": "ignore",
        "env_prefix": "",
    }


# Create a single instance of settings to be imported throughout the app
# Settings instance will load values from .env and environment variables
settings = Settings()  # type: ignore

__all__ = ["settings"]

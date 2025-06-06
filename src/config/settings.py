"""
Centralized configuration management for the application.

This module provides a single source of truth for all environment variables
and configuration settings used throughout the application.
"""
import os
from typing import Optional
from pydantic import Field, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable fallbacks."""
    
    # N8N Configuration
    N8N_WEBHOOK_BASE_URL: str = Field(
        ...,
        env="N8N_WEBHOOK_BASE_URL",
        description="Base URL for n8n webhooks (e.g., 'https://your-n8n-instance.com')"
    )
    N8N_API_KEY: Optional[str] = Field(
        default=None,
        env="N8N_API_KEY",
        description="API key for n8n authentication"
    )
    N8N_ENV: str = Field(
        default="development",
        env="N8N_ENV",
        description="Environment (development, test, staging, production)"
    )
    
    # LLM Configuration
    CLAUDE_API_KEY: Optional[str] = Field(
        None,
        env="CLAUDE_API_KEY",
        description="API key for Anthropic's Claude API"
    )
    CLAUDE_MODEL: str = Field(
        "claude-3-opus-20240229",
        env="CLAUDE_MODEL",
        description="Claude model to use (e.g., 'claude-3-opus-20240229')"
    )
    
    # Logging Configuration
    LOG_LEVEL: str = Field(
        "INFO",
        env="LOG_LEVEL",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    )
    
    @validator('N8N_ENV')
    def validate_environment(cls, v):
        """Ensure environment is one of the allowed values."""
        allowed = {'test', 'development', 'staging', 'production'}
        if v not in allowed:
            raise ValueError(f"N8N_ENV must be one of {allowed}")
        return v
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"  # Ignore extra environment variables


# Create a single instance of settings to be imported throughout the app
settings = Settings()

__all__ = ['settings']

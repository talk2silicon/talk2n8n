"""
Tests for configuration module.
"""

import pytest
from unittest.mock import patch
from talk2n8n.config.settings import Settings


def test_settings_creation():
    """Test that Settings can be created with default values."""
    with patch.dict(
        "os.environ",
        {
            "N8N_WEBHOOK_BASE_URL": "https://test.example.com",
            "CLAUDE_API_KEY": "test-api-key",
            "CLAUDE_MODEL": "claude-3-opus-20240229",
            "LOG_LEVEL": "INFO",  # Explicitly set LOG_LEVEL for test
        },
        clear=True,
    ):
        settings = Settings()
        assert settings.N8N_WEBHOOK_BASE_URL == "https://test.example.com"
        assert settings.CLAUDE_API_KEY == "test-api-key"
        assert settings.CLAUDE_MODEL == "claude-3-opus-20240229"
        assert settings.LOG_LEVEL == "INFO"


def test_settings_validation():
    """Test that N8N_ENV validation works correctly."""
    with patch.dict(
        "os.environ",
        {
            "N8N_WEBHOOK_BASE_URL": "https://test.example.com",
            "CLAUDE_API_KEY": "test-api-key",
            "CLAUDE_MODEL": "claude-3-opus-20240229",
            "N8N_ENV": "invalid_env",
        },
        clear=True,
    ):
        with pytest.raises(ValueError, match="N8N_ENV must be one of"):
            Settings()


def test_settings_valid_environments():
    """Test that valid N8N_ENV values are accepted."""
    valid_envs = ["test", "development", "staging", "production"]
    for env in valid_envs:
        with patch.dict(
            "os.environ",
            {
                "N8N_WEBHOOK_BASE_URL": "https://test.example.com",
                "CLAUDE_API_KEY": "test-api-key",
                "CLAUDE_MODEL": "claude-3-opus-20240229",
                "N8N_ENV": env,
            },
            clear=True,
        ):
            settings = Settings()
            assert settings.N8N_ENV == env

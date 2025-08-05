"""Logging configuration for talk2n8n."""

import logging.config
import os
from pathlib import Path

# Create logs directory if it doesn't exist
logs_dir = Path(__file__).parent.parent.parent / "logs"
logs_dir.mkdir(exist_ok=True)

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {"format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"},
        "detailed": {"format": "%(asctime)s [%(levelname)s] %(name)s:%(lineno)d: %(message)s"},
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "standard",
            "stream": "ext://sys.stdout",
        },
        "agent_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "DEBUG",
            "formatter": "detailed",
            "filename": os.path.join(logs_dir, "agent_debug.log"),
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
            "encoding": "utf8",
        },
        "test_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "DEBUG",
            "formatter": "detailed",
            "filename": os.path.join(logs_dir, "test_debug.log"),
            "maxBytes": 10485760,  # 10MB
            "backupCount": 3,
            "encoding": "utf8",
        },
    },
    "loggers": {
        "": {  # Root logger
            "handlers": ["console"],
            "level": "INFO",
        },
        "talk2n8n.agent": {
            "handlers": ["agent_file", "console"],
            "level": "DEBUG",
            "propagate": False,
        },
        "talk2n8n.tests": {
            "handlers": ["test_file", "console"],
            "level": "DEBUG",
            "propagate": False,
        },
    },
}


def setup_logging():
    """Set up logging configuration."""
    logging.config.dictConfig(LOGGING_CONFIG)

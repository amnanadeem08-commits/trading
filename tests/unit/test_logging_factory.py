"""Unit tests for structured logging factory."""

from __future__ import annotations

import pytest

from config.settings import LoggingSettings
from platform_logging import create_logger
from platform_logging.logger import ContextLogger


@pytest.mark.unit
def test_create_logger_from_settings() -> None:
    settings = LoggingSettings(
        level="INFO",
        format="text",
        include_correlation_id=True,
        console_enabled=True,
    )
    logger = create_logger(settings, service_name="platform")
    assert isinstance(logger, ContextLogger)

"""Configuration tests for operational YAML settings."""

from __future__ import annotations

import pytest

from config.settings import AppSettings, reset_settings


@pytest.fixture(autouse=True)
def _reset_settings() -> None:
    reset_settings()
    yield
    reset_settings()


@pytest.mark.unit
def test_load_monitoring_yaml() -> None:
    settings = AppSettings.from_sources()
    assert settings.monitoring.enabled is True
    assert settings.monitoring.heartbeat_interval_seconds == 30


@pytest.mark.unit
def test_load_security_yaml() -> None:
    settings = AppSettings.from_sources()
    assert settings.security.rbac_enabled is False
    assert settings.security.encryption_algorithm == "aes-256-gcm"


@pytest.mark.unit
def test_load_notifications_yaml() -> None:
    settings = AppSettings.from_sources()
    assert settings.notifications.enabled is False
    assert settings.notifications.default_channel == "webhook"


@pytest.mark.unit
def test_logging_settings_include_trace_and_request_ids() -> None:
    settings = AppSettings.from_sources()
    assert settings.logging.include_trace_id is True
    assert settings.logging.include_request_id is True

"""Unit tests for configuration system."""

from __future__ import annotations

import pytest

from config.loader import load_yaml_config, merge_configs
from config.settings import AppSettings, get_settings, reset_settings
from models.common import ConfigurationError


@pytest.fixture(autouse=True)
def _reset_settings_cache() -> None:
    reset_settings()
    yield
    reset_settings()


@pytest.mark.unit
def test_load_indicators_yaml() -> None:
    data = load_yaml_config("indicators.yaml")
    assert data["indicators"]["rsi_period"] == 14


@pytest.mark.unit
def test_load_missing_yaml_raises() -> None:
    with pytest.raises(ConfigurationError):
        load_yaml_config("nonexistent.yaml")


@pytest.mark.unit
def test_merge_configs_deep_merge() -> None:
    merged = merge_configs(
        {"risk": {"registry_enabled": True}},
        {"risk": {"max_engines": 50}},
    )
    assert merged["risk"]["registry_enabled"] is True
    assert merged["risk"]["max_engines"] == 50


@pytest.mark.unit
def test_app_settings_from_sources() -> None:
    settings = AppSettings.from_sources()
    assert settings.indicators.rsi_period == 14
    assert settings.risk.registry_enabled is True
    assert settings.risk.validation_enabled is True
    assert settings.feature_flags.signal_only is True
    assert settings.feature_flags.live_trading_enabled is False
    assert settings.schema_version == "1.0.0"


@pytest.mark.unit
def test_get_settings_is_cached() -> None:
    first = get_settings()
    second = get_settings()
    assert first is second


@pytest.mark.unit
def test_feature_flags_defaults_are_safe() -> None:
    settings = get_settings()
    assert settings.feature_flags.signal_only is True
    assert settings.feature_flags.live_trading_enabled is False
    assert settings.feature_flags.pmex_enabled is False
    assert settings.feature_flags.experimental_mode is False

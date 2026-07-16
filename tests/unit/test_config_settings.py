"""Unit tests for configuration system."""

from __future__ import annotations

import os

import pytest
from dotenv import dotenv_values

import config.settings as settings_module
from config.loader import load_yaml_config, merge_configs
from config.settings import _ENV_PATH, AppSettings, get_settings, reset_settings
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
def test_project_env_resolves_from_repository_root() -> None:
    assert _ENV_PATH.resolve() == (settings_module._PROJECT_ROOT / ".env").resolve()


@pytest.mark.unit
def test_binance_credentials_load_without_printing_values() -> None:
    settings_module.load_project_env()
    expected_key = str(
        dotenv_values(_ENV_PATH, encoding="utf-8-sig").get("BINANCE_API_KEY")
        or dotenv_values(settings_module._ENV_TXT_PATH, encoding="utf-8-sig").get("BINANCE_API_KEY")
        or ""
    ).strip()
    expected_secret = str(
        dotenv_values(_ENV_PATH, encoding="utf-8-sig").get("BINANCE_API_SECRET")
        or dotenv_values(settings_module._ENV_TXT_PATH, encoding="utf-8-sig").get(
            "BINANCE_API_SECRET"
        )
        or ""
    ).strip()
    key_loaded = bool(os.getenv("BINANCE_API_KEY", "").strip())
    secret_loaded = bool(os.getenv("BINANCE_API_SECRET", "").strip())
    if expected_key and expected_secret:
        assert key_loaded
        assert secret_loaded
    else:
        assert not key_loaded or not secret_loaded


@pytest.mark.unit
def test_feature_flags_defaults_are_safe() -> None:
    settings = get_settings()
    assert settings.feature_flags.signal_only is True
    assert settings.feature_flags.live_trading_enabled is False
    assert settings.feature_flags.pmex_enabled is False
    assert settings.feature_flags.experimental_mode is False


@pytest.mark.unit
@pytest.mark.parametrize(
    "portfolio_payload",
    [
        ConfigurationError("missing portfolio config"),
        {"portfolio_sync": {"minimum_holding_usdt": "invalid"}},
    ],
)
def test_portfolio_settings_fall_back_when_yaml_is_missing_or_invalid(
    monkeypatch: pytest.MonkeyPatch,
    portfolio_payload: Exception | dict[str, object],
) -> None:
    original_loader = settings_module.load_yaml_config

    def fake_loader(filename: str) -> dict[str, object]:
        if filename != "portfolio_sync.yaml":
            return original_loader(filename)
        if isinstance(portfolio_payload, Exception):
            raise portfolio_payload
        return portfolio_payload

    monkeypatch.setattr(settings_module, "load_yaml_config", fake_loader)
    settings = AppSettings.from_sources()
    assert settings.portfolio_sync.portfolio_sync_enabled is False
    assert settings.portfolio_sync.enabled is False
    assert settings.portfolio_sync.minimum_holding_usdt == 1.0
    assert settings.portfolio_sync.quote_asset == "USDT"
    assert settings.portfolio_sync.timeout_milliseconds == 10_000
    assert settings.portfolio_sync.api_timeout_seconds == 10.0
    assert settings.portfolio_sync.sync_timeout_seconds == 30.0
    assert settings.portfolio_sync.cache_ttl_seconds == 300.0
    assert settings.portfolio_sync.max_retries == 1
    assert settings.portfolio_sync.asset_analysis_mapping == {"BNSOL": "SOL/USDT"}

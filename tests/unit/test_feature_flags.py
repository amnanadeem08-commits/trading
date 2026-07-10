"""Unit tests for feature flag manager."""

from __future__ import annotations

import pytest

from feature_flags import (
    FeatureFlagDefaults,
    FeatureFlagManager,
    FeatureFlagName,
    reset_feature_flag_manager,
)
from feature_flags.providers import EnvironmentFeatureFlagProvider


@pytest.fixture(autouse=True)
def _reset_flags() -> None:
    reset_feature_flag_manager()
    yield
    reset_feature_flag_manager()


@pytest.mark.unit
def test_defaults_are_production_safe() -> None:
    defaults = FeatureFlagDefaults()
    assert defaults.is_enabled(FeatureFlagName.SIGNAL_ONLY) is True
    assert defaults.is_enabled(FeatureFlagName.LIVE_TRADING_ENABLED) is False
    assert defaults.is_enabled(FeatureFlagName.PMEX_ENABLED) is False
    assert defaults.is_enabled(FeatureFlagName.EXPERIMENTAL_MODE) is False


@pytest.mark.unit
def test_manager_loads_yaml_flags() -> None:
    manager = FeatureFlagManager()
    flags = manager.refresh()
    assert flags["SIGNAL_ONLY"] is True
    assert flags["AI_ENABLED"] is True
    assert flags["RAG_ENABLED"] is False


@pytest.mark.unit
def test_environment_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FEATURE_FLAG_RAG_ENABLED", "true")
    provider = EnvironmentFeatureFlagProvider()
    assert provider.resolve()["RAG_ENABLED"] is True


@pytest.mark.unit
def test_manager_is_enabled_and_require_enabled() -> None:
    manager = FeatureFlagManager()
    manager.refresh()
    assert manager.is_enabled(FeatureFlagName.SIGNAL_ONLY) is True
    with pytest.raises(PermissionError):
        manager.require_enabled(FeatureFlagName.LIVE_TRADING_ENABLED)


@pytest.mark.unit
def test_unknown_flag_raises_key_error() -> None:
    manager = FeatureFlagManager()
    manager.refresh()
    with pytest.raises(KeyError):
        manager.is_enabled("UNKNOWN_FLAG")

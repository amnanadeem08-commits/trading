"""Unit tests for paper adapter configuration."""

from __future__ import annotations

import pytest

from config.settings import get_settings, reset_settings
from connectors import PaperSettings
from connectors.adapters.paper.paper_settings import PaperSettings as RuntimePaperSettings


@pytest.fixture(autouse=True)
def _reset_settings() -> None:
    reset_settings()
    yield
    reset_settings()


def test_paper_adapter_yaml_loaded() -> None:
    settings = get_settings()
    assert settings.paper_adapter.enabled is True
    assert settings.paper_adapter.deterministic is True
    assert settings.paper_adapter.random_seed == 42
    assert settings.paper_adapter.failure_rate == 0.0
    assert settings.paper_adapter.latency_ms_min == 1
    assert settings.paper_adapter.latency_ms_max == 50
    assert settings.paper_adapter.simulate_delay is False


def test_paper_settings_runtime_model() -> None:
    runtime = RuntimePaperSettings(
        enabled=True,
        deterministic=True,
        random_seed=10,
        failure_rate=0.1,
        latency_ms_min=2,
        latency_ms_max=8,
    )
    assert runtime.latency_ms_max >= runtime.latency_ms_min


def test_paper_settings_invalid_latency_bounds() -> None:
    with pytest.raises(ValueError, match="latency_ms_max"):
        RuntimePaperSettings(latency_ms_min=10, latency_ms_max=1)


def test_platform_settings_map_to_runtime() -> None:
    platform = get_settings().paper_adapter
    runtime = PaperSettings(**platform.model_dump())
    assert runtime.enabled == platform.enabled
    assert runtime.random_seed == platform.random_seed

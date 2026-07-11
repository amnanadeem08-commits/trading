"""Config and public API smoke tests for signal_engine."""

from __future__ import annotations

import pytest

from config.settings import AppSettings, reset_settings
from signal_engine import SignalAssembler, SignalAssemblyRequest, SignalRegistry


@pytest.mark.unit
def test_signal_engine_settings_load_from_yaml() -> None:
    reset_settings()
    settings = AppSettings.from_sources()
    assert settings.signal_engine.registry_enabled is True
    assert settings.signal_engine.max_signals == 10_000
    assert settings.signal_engine.assembly_enabled is True
    reset_settings()


@pytest.mark.unit
def test_public_api_exports() -> None:
    assert SignalAssembler is not None
    assert SignalAssemblyRequest is not None
    assert SignalRegistry is not None

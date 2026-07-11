"""Unit tests for SignalRegistry."""

from __future__ import annotations

import pytest

from signal_engine import (
    SignalAssembler,
    SignalNotFoundError,
    SignalRegistrationError,
    SignalRegistry,
    get_signal_registry,
    reset_signal_registry,
)
from tests.signal_helpers import make_assembly_request


@pytest.fixture(autouse=True)
def _reset_default_registry() -> None:
    reset_signal_registry()
    yield
    reset_signal_registry()


@pytest.mark.unit
def test_registry_register_and_get() -> None:
    registry = SignalRegistry()
    signal = SignalAssembler().assemble(make_assembly_request())
    record = registry.register(signal)
    assert record.signal_id == "sig-1"
    assert registry.get("sig-1").signal.signal_id == "sig-1"
    assert registry.list_ids() == ("sig-1",)
    assert registry.size == 1


@pytest.mark.unit
def test_registry_rejects_duplicate_ids() -> None:
    registry = SignalRegistry()
    signal = SignalAssembler().assemble(make_assembly_request())
    registry.register(signal)
    with pytest.raises(SignalRegistrationError, match="already registered"):
        registry.register(signal)


@pytest.mark.unit
def test_registry_capacity_and_missing() -> None:
    registry = SignalRegistry(max_signals=1)
    signal = SignalAssembler().assemble(make_assembly_request())
    registry.register(signal)
    with pytest.raises(SignalRegistrationError, match="capacity"):
        registry.register(SignalAssembler().assemble(make_assembly_request(signal_id="sig-2")))
    with pytest.raises(SignalNotFoundError):
        registry.get("missing")
    registry.clear()
    assert registry.size == 0


@pytest.mark.unit
def test_registry_rejects_invalid_capacity() -> None:
    with pytest.raises(SignalRegistrationError, match="max_signals"):
        SignalRegistry(max_signals=0)

    first = get_signal_registry()
    second = get_signal_registry()
    assert first is second
    reset_signal_registry()
    third = get_signal_registry()
    assert third is not first

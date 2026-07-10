"""Unit tests for adapter factory."""

from __future__ import annotations

import pytest

from framework_adapters import AdapterFactory, AdapterFactoryError, EngineType
from tests.framework_adapters_helpers import register_stub_adapter_factory


@pytest.mark.unit
def test_adapter_factory_create_stub() -> None:
    factory = AdapterFactory()
    register_stub_adapter_factory(factory)
    adapter = factory.create(EngineType.STUB)
    assert adapter.engine_type() == EngineType.STUB


@pytest.mark.unit
def test_adapter_factory_missing_engine_type() -> None:
    factory = AdapterFactory()
    with pytest.raises(AdapterFactoryError):
        factory.create(EngineType.PYTORCH)


@pytest.mark.unit
def test_adapter_factory_clear() -> None:
    factory = AdapterFactory()
    register_stub_adapter_factory(factory)
    factory.clear()
    with pytest.raises(AdapterFactoryError):
        factory.create(EngineType.STUB)

"""Adapter factory."""

from __future__ import annotations

from collections.abc import Callable

from framework_adapters.contracts.engine_type import EngineType
from framework_adapters.contracts.framework_adapter import FrameworkAdapter
from framework_adapters.exceptions import AdapterFactoryError

type AdapterFactoryCallable = Callable[[], FrameworkAdapter]


class AdapterFactory:
    """Creates framework adapter instances without framework logic."""

    def __init__(self) -> None:
        self._factories: dict[EngineType, AdapterFactoryCallable] = {}

    def register(self, engine_type: EngineType, factory: AdapterFactoryCallable) -> None:
        self._factories[engine_type] = factory

    def create(self, engine_type: EngineType) -> FrameworkAdapter:
        factory = self._factories.get(engine_type)
        if factory is None:
            msg = f"No adapter factory registered for engine type: {engine_type.value}"
            raise AdapterFactoryError(msg)
        return factory()

    def supported_engine_types(self) -> tuple[EngineType, ...]:
        return tuple(sorted(self._factories, key=lambda item: item.value))

    def clear(self) -> None:
        self._factories.clear()

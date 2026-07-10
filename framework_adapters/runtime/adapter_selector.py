"""Adapter selection by engine type, format, and priority."""

from __future__ import annotations

import time

from framework_adapters.exceptions import AdapterResolutionError
from framework_adapters.registry.adapter_record import AdapterRecord
from framework_adapters.registry.adapter_registry import AdapterRegistry
from framework_adapters.runtime.adapter_runtime_context import AdapterRuntimeContext


class AdapterSelector:
    """Selects the best registered adapter for a runtime context."""

    def select(
        self,
        registry: AdapterRegistry,
        *,
        context: AdapterRuntimeContext,
        default_adapter_id: str | None = None,
    ) -> tuple[AdapterRecord, float]:
        """Return the selected adapter record and selection latency in milliseconds."""
        started = time.monotonic() * 1000.0
        candidates = registry.list_by_engine_type(context.engine_type)
        if not candidates:
            msg = f"No adapters registered for engine type: {context.engine_type.value}"
            raise AdapterResolutionError(msg)

        filtered = self._filter_by_artifact_format(candidates, context.artifact_format)
        if not filtered:
            msg = (
                f"No adapters support artifact format '{context.artifact_format}' "
                f"for engine type: {context.engine_type.value}"
            )
            raise AdapterResolutionError(msg)

        selected = self._select_by_priority(filtered, default_adapter_id=default_adapter_id)
        latency_ms = max(0.0, time.monotonic() * 1000.0 - started)
        return selected, latency_ms

    def _filter_by_artifact_format(
        self,
        candidates: tuple[AdapterRecord, ...],
        artifact_format: str,
    ) -> tuple[AdapterRecord, ...]:
        if not artifact_format.strip():
            return candidates
        matched = tuple(
            record
            for record in candidates
            if artifact_format in record.manifest.supported_artifact_formats
            or not record.manifest.supported_artifact_formats
        )
        return matched or candidates

    def _select_by_priority(
        self,
        candidates: tuple[AdapterRecord, ...],
        *,
        default_adapter_id: str | None,
    ) -> AdapterRecord:
        if default_adapter_id is not None:
            for record in candidates:
                if record.adapter_id == default_adapter_id:
                    return record

        return max(candidates, key=lambda record: record.priority)

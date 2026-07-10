"""Adapter metrics collection."""

from __future__ import annotations

from threading import RLock

from framework_adapters.contracts.framework_adapter import FrameworkAdapter
from framework_adapters.metrics.adapter_statistics import AdapterStatistics
from framework_adapters.metrics.adapter_summary import AdapterSummary
from framework_adapters.registry.adapter_record import AdapterState


class AdapterMetricsCollector:
    """Collects framework adapter metrics without external backends."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._state_counts: dict[AdapterState, int] = {state: 0 for state in AdapterState}
        self._summaries: dict[str, AdapterSummary] = {}
        self._validations = 0
        self._loads = 0
        self._shutdowns = 0
        self._failures = 0
        self._usage: dict[str, int] = {}
        self._executions = 0
        self._load_time_ms = 0.0
        self._selection_latency_ms = 0.0
        self._model_loads = 0
        self._model_reloads = 0
        self._model_unloads = 0
        self._cache_hits = 0
        self._cache_misses = 0
        self._warm_start_duration_ms = 0.0
        self._initialization_latency_ms = 0.0
        self._session_reuse_count = 0
        self._failed_model_loads = 0

    def record_state(self, state: AdapterState) -> None:
        with self._lock:
            self._state_counts[state] = self._state_counts.get(state, 0) + 1

    def record_validation(self) -> None:
        with self._lock:
            self._validations += 1

    def record_load(self) -> None:
        with self._lock:
            self._loads += 1

    def record_shutdown(self) -> None:
        with self._lock:
            self._shutdowns += 1

    def record_failure(self) -> None:
        with self._lock:
            self._failures += 1

    def record_usage(self, adapter_id: str) -> None:
        with self._lock:
            self._usage[adapter_id] = self._usage.get(adapter_id, 0) + 1

    def record_execution(self) -> None:
        with self._lock:
            self._executions += 1

    def record_load_time(self, load_time_ms: float) -> None:
        with self._lock:
            self._load_time_ms += max(0.0, load_time_ms)

    def record_selection_latency(self, latency_ms: float) -> None:
        with self._lock:
            self._selection_latency_ms += max(0.0, latency_ms)

    def record_model_load(self) -> None:
        with self._lock:
            self._model_loads += 1

    def record_model_reload(self) -> None:
        with self._lock:
            self._model_reloads += 1

    def record_model_unload(self) -> None:
        with self._lock:
            self._model_unloads += 1

    def record_cache_hit(self) -> None:
        with self._lock:
            self._cache_hits += 1

    def record_cache_miss(self) -> None:
        with self._lock:
            self._cache_misses += 1

    def record_warm_start_duration(self, duration_ms: float) -> None:
        with self._lock:
            self._warm_start_duration_ms += max(0.0, duration_ms)

    def record_initialization_latency(self, latency_ms: float) -> None:
        with self._lock:
            self._initialization_latency_ms += max(0.0, latency_ms)

    def record_session_reuse(self) -> None:
        with self._lock:
            self._session_reuse_count += 1

    def record_failed_model_load(self) -> None:
        with self._lock:
            self._failed_model_loads += 1

    def record_summary(self, summary: AdapterSummary) -> None:
        with self._lock:
            self._summaries[summary.adapter_id] = summary

    def record_summary_from_adapter(
        self,
        adapter: FrameworkAdapter,
        *,
        state: AdapterState,
    ) -> None:
        metadata = adapter.metadata()
        self.record_summary(
            AdapterSummary(
                adapter_id=adapter.adapter_id(),
                name=metadata.name,
                version=metadata.version,
                state=state,
                engine_type=metadata.engine_type,
            )
        )

    def statistics(self) -> AdapterStatistics:
        with self._lock:
            total = sum(self._state_counts.values())
            return AdapterStatistics(
                total_adapters=total,
                discovered_adapters=self._state_counts.get(AdapterState.DISCOVERED, 0),
                registered_adapters=self._state_counts.get(AdapterState.REGISTERED, 0),
                validated_adapters=self._state_counts.get(AdapterState.VALIDATED, 0),
                loaded_adapters=self._state_counts.get(AdapterState.LOADED, 0),
                healthy_adapters=self._state_counts.get(AdapterState.HEALTHY, 0),
                failed_adapters=self._state_counts.get(AdapterState.FAILED, 0),
                shutdown_adapters=self._state_counts.get(AdapterState.SHUTDOWN, 0),
                adapter_validations=self._validations,
                adapter_loads=self._loads,
                adapter_shutdowns=self._shutdowns,
                adapter_failures=self._failures,
                adapter_usage=sum(self._usage.values()),
                adapter_executions=self._executions,
                adapter_load_time_ms=self._load_time_ms,
                adapter_selection_latency_ms=self._selection_latency_ms,
                model_load_count=self._model_loads,
                model_reload_count=self._model_reloads,
                model_unload_count=self._model_unloads,
                cache_hits=self._cache_hits,
                cache_misses=self._cache_misses,
                warm_start_duration_ms=self._warm_start_duration_ms,
                initialization_latency_ms=self._initialization_latency_ms,
                session_reuse_count=self._session_reuse_count,
                failed_model_loads=self._failed_model_loads,
            )

    def get_summary(self, adapter_id: str) -> AdapterSummary | None:
        with self._lock:
            return self._summaries.get(adapter_id)

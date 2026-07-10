"""Adapter statistics contracts."""

from __future__ import annotations

from models.common import PlatformModel


class AdapterStatistics(PlatformModel):
    """Aggregate statistics for framework adapters."""

    total_adapters: int
    discovered_adapters: int
    registered_adapters: int
    validated_adapters: int
    loaded_adapters: int
    healthy_adapters: int
    failed_adapters: int
    shutdown_adapters: int
    adapter_validations: int
    adapter_loads: int
    adapter_shutdowns: int
    adapter_failures: int
    adapter_usage: int = 0
    adapter_executions: int = 0
    adapter_load_time_ms: float = 0.0
    adapter_selection_latency_ms: float = 0.0
    model_load_count: int = 0
    model_reload_count: int = 0
    model_unload_count: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    warm_start_duration_ms: float = 0.0
    initialization_latency_ms: float = 0.0
    session_reuse_count: int = 0
    failed_model_loads: int = 0

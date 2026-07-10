"""Provider metrics collection."""

from __future__ import annotations

from threading import RLock

from storage_providers.contracts.storage_provider import StorageProvider
from storage_providers.metrics.provider_statistics import ProviderStatistics
from storage_providers.metrics.provider_summary import ProviderSummary
from storage_providers.registry.provider_record import ProviderState


class ProviderMetricsCollector:
    """Collects storage provider metrics without external backends."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._state_counts: dict[ProviderState, int] = {state: 0 for state in ProviderState}
        self._summaries: dict[str, ProviderSummary] = {}
        self._registrations = 0
        self._resolutions = 0
        self._validations = 0
        self._failures = 0
        self._cache_hits = 0
        self._cache_misses = 0
        self._validation_failures = 0
        self._resolution_failures = 0
        self._filesystem_lookups = 0
        self._checksum_operations = 0
        self._missing_files = 0
        self._invalid_paths = 0
        self._provider_usage: dict[str, int] = {}

    def record_state(self, state: ProviderState) -> None:
        with self._lock:
            self._state_counts[state] = self._state_counts.get(state, 0) + 1

    def record_registration(self) -> None:
        with self._lock:
            self._registrations += 1

    def record_resolution(self) -> None:
        with self._lock:
            self._resolutions += 1

    def record_validation(self) -> None:
        with self._lock:
            self._validations += 1

    def record_failure(self) -> None:
        with self._lock:
            self._failures += 1

    def record_validation_failure(self) -> None:
        with self._lock:
            self._validation_failures += 1
            self._failures += 1

    def record_resolution_failure(self) -> None:
        with self._lock:
            self._resolution_failures += 1
            self._failures += 1

    def record_cache_hit(self) -> None:
        with self._lock:
            self._cache_hits += 1

    def record_cache_miss(self) -> None:
        with self._lock:
            self._cache_misses += 1

    def record_provider_usage(self, provider_id: str) -> None:
        with self._lock:
            self._provider_usage[provider_id] = self._provider_usage.get(provider_id, 0) + 1

    def record_filesystem_lookup(self) -> None:
        with self._lock:
            self._filesystem_lookups += 1

    def record_checksum_operation(self) -> None:
        with self._lock:
            self._checksum_operations += 1

    def record_missing_file(self) -> None:
        with self._lock:
            self._missing_files += 1

    def record_invalid_path(self) -> None:
        with self._lock:
            self._invalid_paths += 1

    def record_summary(self, summary: ProviderSummary) -> None:
        with self._lock:
            self._summaries[summary.provider_id] = summary

    def record_summary_from_provider(
        self,
        provider: StorageProvider,
        *,
        state: ProviderState,
        uri_scheme: str = "",
    ) -> None:
        metadata = provider.metadata()
        self.record_summary(
            ProviderSummary(
                provider_id=provider.provider_id(),
                name=metadata.name,
                version=metadata.version,
                state=state,
                provider_type=provider.provider_type(),
                uri_scheme=uri_scheme,
            )
        )

    def statistics(self) -> ProviderStatistics:
        with self._lock:
            total = sum(self._state_counts.values())
            return ProviderStatistics(
                total_providers=total,
                registered_providers=self._state_counts.get(ProviderState.REGISTERED, 0),
                validated_providers=self._state_counts.get(ProviderState.VALIDATED, 0),
                resolved_providers=self._state_counts.get(ProviderState.RESOLVED, 0),
                healthy_providers=self._state_counts.get(ProviderState.HEALTHY, 0),
                failed_providers=self._state_counts.get(ProviderState.FAILED, 0),
                shutdown_providers=self._state_counts.get(ProviderState.SHUTDOWN, 0),
                provider_registrations=self._registrations,
                provider_resolutions=self._resolutions,
                provider_validations=self._validations,
                provider_failures=self._failures,
                provider_usage=dict(self._provider_usage),
                cache_hits=self._cache_hits,
                cache_misses=self._cache_misses,
                validation_failures=self._validation_failures,
                resolution_failures=self._resolution_failures,
                filesystem_lookups=self._filesystem_lookups,
                checksum_operations=self._checksum_operations,
                missing_files=self._missing_files,
                invalid_paths=self._invalid_paths,
            )

    def get_summary(self, provider_id: str) -> ProviderSummary | None:
        with self._lock:
            return self._summaries.get(provider_id)

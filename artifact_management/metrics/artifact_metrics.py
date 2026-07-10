"""Artifact metrics collection."""

from __future__ import annotations

from threading import RLock

from artifact_management.metrics.artifact_statistics import ArtifactStatistics
from artifact_management.metrics.artifact_summary import ArtifactSummary
from artifact_management.registry.artifact_record import ArtifactState


class ArtifactMetricsCollector:
    """Collects artifact management metrics without external backends."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._state_counts: dict[ArtifactState, int] = {state: 0 for state in ArtifactState}
        self._summaries: dict[str, ArtifactSummary] = {}
        self._registrations = 0
        self._resolutions = 0
        self._validations = 0
        self._cache_hits = 0
        self._cache_misses = 0
        self._failures = 0

    def record_state(self, state: ArtifactState) -> None:
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

    def record_cache_hit(self) -> None:
        with self._lock:
            self._cache_hits += 1

    def record_cache_miss(self) -> None:
        with self._lock:
            self._cache_misses += 1

    def record_failure(self) -> None:
        with self._lock:
            self._failures += 1

    def record_summary(self, summary: ArtifactSummary) -> None:
        with self._lock:
            self._summaries[summary.artifact_id] = summary

    def statistics(self) -> ArtifactStatistics:
        with self._lock:
            total = sum(self._state_counts.values())
            return ArtifactStatistics(
                total_artifacts=total,
                registered_artifacts=self._state_counts.get(ArtifactState.REGISTERED, 0),
                resolved_artifacts=self._state_counts.get(ArtifactState.RESOLVED, 0),
                validated_artifacts=self._state_counts.get(ArtifactState.VALIDATED, 0),
                cached_artifacts=self._state_counts.get(ArtifactState.CACHED, 0),
                expired_artifacts=self._state_counts.get(ArtifactState.EXPIRED, 0),
                failed_artifacts=self._state_counts.get(ArtifactState.FAILED, 0),
                artifact_registrations=self._registrations,
                artifact_resolutions=self._resolutions,
                artifact_validations=self._validations,
                cache_hits=self._cache_hits,
                cache_misses=self._cache_misses,
                artifact_failures=self._failures,
            )

    def get_summary(self, artifact_id: str) -> ArtifactSummary | None:
        with self._lock:
            return self._summaries.get(artifact_id)

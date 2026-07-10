"""Inference metrics collection."""

from __future__ import annotations

from threading import RLock

from inference_pipeline.responses.inference_result import InferenceStatus
from models.common import PlatformModel


class InferenceStatistics(PlatformModel):
    """Aggregate inference statistics."""

    total_requests: int = 0
    queued_requests: int = 0
    running_requests: int = 0
    completed_requests: int = 0
    failed_requests: int = 0
    cancelled_requests: int = 0
    total_latency_ms: float = 0.0
    total_queue_time_ms: float = 0.0
    throughput_per_minute: float = 0.0
    feature_mapping_ms: float = 0.0
    input_binding_ms: float = 0.0
    execution_latency_ms: float = 0.0
    output_normalization_ms: float = 0.0
    total_inference_latency_ms: float = 0.0
    validation_failures: int = 0


class InferenceSummary(PlatformModel):
    """Summary for a single inference request."""

    request_id: str
    model_id: str
    status: InferenceStatus
    latency_ms: float = 0.0
    queue_time_ms: float = 0.0


class InferenceMetricsCollector:
    """Collects inference pipeline metrics."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._status_counts: dict[InferenceStatus, int] = {status: 0 for status in InferenceStatus}
        self._total_latency_ms = 0.0
        self._total_queue_time_ms = 0.0
        self._summaries: dict[str, InferenceSummary] = {}
        self._feature_mapping_ms = 0.0
        self._input_binding_ms = 0.0
        self._execution_latency_ms = 0.0
        self._output_normalization_ms = 0.0
        self._total_inference_latency_ms = 0.0
        self._validation_failures = 0

    def record_status(self, status: InferenceStatus) -> None:
        with self._lock:
            self._status_counts[status] = self._status_counts.get(status, 0) + 1

    def record_latency(self, latency_ms: float, *, queue_time_ms: float = 0.0) -> None:
        with self._lock:
            self._total_latency_ms += latency_ms
            self._total_queue_time_ms += queue_time_ms

    def record_feature_mapping(self, duration_ms: float) -> None:
        with self._lock:
            self._feature_mapping_ms += max(0.0, duration_ms)

    def record_input_binding(self, duration_ms: float) -> None:
        with self._lock:
            self._input_binding_ms += max(0.0, duration_ms)

    def record_execution_latency(self, duration_ms: float) -> None:
        with self._lock:
            self._execution_latency_ms += max(0.0, duration_ms)

    def record_output_normalization(self, duration_ms: float) -> None:
        with self._lock:
            self._output_normalization_ms += max(0.0, duration_ms)

    def record_total_inference_latency(self, duration_ms: float) -> None:
        with self._lock:
            self._total_inference_latency_ms += max(0.0, duration_ms)

    def record_validation_failure(self) -> None:
        with self._lock:
            self._validation_failures += 1

    def record_summary(self, summary: InferenceSummary) -> None:
        with self._lock:
            self._summaries[summary.request_id] = summary

    def statistics(self) -> InferenceStatistics:
        with self._lock:
            total = sum(self._status_counts.values())
            completed = self._status_counts.get(InferenceStatus.COMPLETED, 0)
            throughput = (completed / max(total, 1)) * 60.0
            return InferenceStatistics(
                total_requests=total,
                queued_requests=self._status_counts.get(InferenceStatus.QUEUED, 0),
                running_requests=self._status_counts.get(InferenceStatus.RUNNING, 0),
                completed_requests=completed,
                failed_requests=self._status_counts.get(InferenceStatus.FAILED, 0),
                cancelled_requests=self._status_counts.get(InferenceStatus.CANCELLED, 0),
                total_latency_ms=self._total_latency_ms,
                total_queue_time_ms=self._total_queue_time_ms,
                throughput_per_minute=throughput,
                feature_mapping_ms=self._feature_mapping_ms,
                input_binding_ms=self._input_binding_ms,
                execution_latency_ms=self._execution_latency_ms,
                output_normalization_ms=self._output_normalization_ms,
                total_inference_latency_ms=self._total_inference_latency_ms,
                validation_failures=self._validation_failures,
            )

    def get_summary(self, request_id: str) -> InferenceSummary | None:
        with self._lock:
            return self._summaries.get(request_id)

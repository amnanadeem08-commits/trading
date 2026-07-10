"""Metric registry for collecting platform metrics."""

from __future__ import annotations

from threading import RLock

from metrics.in_memory import InMemoryCounter, InMemoryGauge, InMemoryHistogram, InMemoryTimer
from metrics.types import Counter, Gauge, Histogram, Timer
from models.common import ContractViolationError


class MetricRegistry:
    """Registry for platform metrics."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._counters: dict[str, Counter] = {}
        self._gauges: dict[str, Gauge] = {}
        self._histograms: dict[str, Histogram] = {}
        self._timers: dict[str, Timer] = {}

    def counter(self, name: str) -> Counter:
        with self._lock:
            if name not in self._counters:
                self._counters[name] = InMemoryCounter(name)
            return self._counters[name]

    def gauge(self, name: str) -> Gauge:
        with self._lock:
            if name not in self._gauges:
                self._gauges[name] = InMemoryGauge(name)
            return self._gauges[name]

    def histogram(self, name: str) -> Histogram:
        with self._lock:
            if name not in self._histograms:
                self._histograms[name] = InMemoryHistogram(name)
            return self._histograms[name]

    def timer(self, name: str) -> Timer:
        with self._lock:
            if name not in self._timers:
                histogram = InMemoryHistogram(f"{name}_duration")
                self._histograms[f"{name}_duration"] = histogram
                self._timers[name] = InMemoryTimer(name, histogram)
            return self._timers[name]

    def list_metrics(self) -> dict[str, tuple[str, ...]]:
        with self._lock:
            return {
                "counters": tuple(sorted(self._counters.keys())),
                "gauges": tuple(sorted(self._gauges.keys())),
                "histograms": tuple(sorted(self._histograms.keys())),
                "timers": tuple(sorted(self._timers.keys())),
            }

    def snapshot(self) -> dict[str, float | int]:
        """Return a flat snapshot of all metric values."""
        result: dict[str, float | int] = {}
        with self._lock:
            for name, counter in self._counters.items():
                result[f"counter:{name}"] = counter.get()
            for name, gauge in self._gauges.items():
                result[f"gauge:{name}"] = gauge.get()
            for name, histogram in self._histograms.items():
                result[f"histogram:{name}:count"] = histogram.count()
                result[f"histogram:{name}:sum"] = histogram.sum()
        return result

    def get_counter(self, name: str) -> Counter:
        with self._lock:
            counter = self._counters.get(name)
        if counter is None:
            msg = f"Counter not registered: {name}"
            raise ContractViolationError(msg)
        return counter

"""In-memory metric implementations for Phase 0."""

from __future__ import annotations

import time
from collections.abc import Iterator
from contextlib import contextmanager
from threading import RLock

from metrics.types import Counter, Gauge, Histogram, Timer


class InMemoryCounter(Counter):
    def __init__(self, name: str) -> None:
        self._name = name
        self._lock = RLock()
        self._value = 0.0

    @property
    def name(self) -> str:
        return self._name

    def inc(self, value: float = 1.0) -> None:
        with self._lock:
            self._value += value

    def get(self) -> float:
        with self._lock:
            return self._value


class InMemoryGauge(Gauge):
    def __init__(self, name: str) -> None:
        self._name = name
        self._lock = RLock()
        self._value = 0.0

    @property
    def name(self) -> str:
        return self._name

    def set(self, value: float) -> None:
        with self._lock:
            self._value = value

    def inc(self, value: float = 1.0) -> None:
        with self._lock:
            self._value += value

    def dec(self, value: float = 1.0) -> None:
        with self._lock:
            self._value -= value

    def get(self) -> float:
        with self._lock:
            return self._value


class InMemoryHistogram(Histogram):
    def __init__(self, name: str) -> None:
        self._name = name
        self._lock = RLock()
        self._observations: list[float] = []

    @property
    def name(self) -> str:
        return self._name

    def observe(self, value: float) -> None:
        with self._lock:
            self._observations.append(value)

    def count(self) -> int:
        with self._lock:
            return len(self._observations)

    def sum(self) -> float:
        with self._lock:
            return sum(self._observations)


class InMemoryTimer(Timer):
    def __init__(self, name: str, histogram: InMemoryHistogram) -> None:
        self._name = name
        self._histogram = histogram

    @property
    def name(self) -> str:
        return self._name

    @contextmanager
    def start(self) -> Iterator[InMemoryTimer]:
        start = time.perf_counter()
        try:
            yield self
        finally:
            self.record(time.perf_counter() - start)

    def record(self, duration_seconds: float) -> None:
        self._histogram.observe(duration_seconds)

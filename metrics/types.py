"""Metric type interfaces for future Prometheus integration."""

from __future__ import annotations

from abc import ABC, abstractmethod
from contextlib import AbstractContextManager
from typing import Self


class Counter(ABC):
    """Monotonically increasing counter metric."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Return metric name."""

    @abstractmethod
    def inc(self, value: float = 1.0) -> None:
        """Increment the counter."""

    @abstractmethod
    def get(self) -> float:
        """Return current counter value."""


class Gauge(ABC):
    """Metric that can increase and decrease."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Return metric name."""

    @abstractmethod
    def set(self, value: float) -> None:
        """Set gauge value."""

    @abstractmethod
    def inc(self, value: float = 1.0) -> None:
        """Increment gauge value."""

    @abstractmethod
    def dec(self, value: float = 1.0) -> None:
        """Decrement gauge value."""

    @abstractmethod
    def get(self) -> float:
        """Return current gauge value."""


class Histogram(ABC):
    """Distribution metric for observed values."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Return metric name."""

    @abstractmethod
    def observe(self, value: float) -> None:
        """Record an observation."""

    @abstractmethod
    def count(self) -> int:
        """Return observation count."""

    @abstractmethod
    def sum(self) -> float:
        """Return sum of observations."""


class Timer(ABC):
    """Duration measurement metric."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Return metric name."""

    @abstractmethod
    def start(self) -> AbstractContextManager[Self]:
        """Return a context manager that records duration on exit."""

    @abstractmethod
    def record(self, duration_seconds: float) -> None:
        """Record a duration in seconds."""

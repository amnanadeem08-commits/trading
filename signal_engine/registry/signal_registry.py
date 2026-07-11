"""In-memory registry for assembled explainable signals."""

from __future__ import annotations

from threading import RLock

from models.signal import ExplainableSignal
from signal_engine.exceptions import SignalNotFoundError, SignalRegistrationError
from signal_engine.registry.signal_record import SignalRecord

_default_signal_registry: SignalRegistry | None = None
_registry_lock = RLock()


class SignalRegistry:
    """Thread-safe registry for assembled signals."""

    def __init__(self, *, max_signals: int = 10_000) -> None:
        if max_signals < 1:
            msg = "max_signals must be >= 1"
            raise SignalRegistrationError(msg)
        self._lock = RLock()
        self._max_signals = max_signals
        self._records: dict[str, SignalRecord] = {}

    def register(self, signal: ExplainableSignal) -> SignalRecord:
        """Register an assembled signal. Duplicate ids are rejected."""
        signal_id = signal.signal_id
        with self._lock:
            if signal_id in self._records:
                msg = f"Signal already registered: {signal_id}"
                raise SignalRegistrationError(msg)
            if len(self._records) >= self._max_signals:
                msg = f"Signal registry capacity exceeded: {self._max_signals}"
                raise SignalRegistrationError(msg)
            record = SignalRecord(signal_id=signal_id, signal=signal)
            self._records[signal_id] = record
            return record

    def get(self, signal_id: str) -> SignalRecord:
        with self._lock:
            record = self._records.get(signal_id)
            if record is None:
                raise SignalNotFoundError(signal_id)
            return record

    def list_ids(self) -> tuple[str, ...]:
        with self._lock:
            return tuple(sorted(self._records))

    def clear(self) -> None:
        with self._lock:
            self._records.clear()

    @property
    def size(self) -> int:
        with self._lock:
            return len(self._records)


def get_signal_registry() -> SignalRegistry:
    """Return the process-wide default signal registry."""
    global _default_signal_registry
    with _registry_lock:
        if _default_signal_registry is None:
            _default_signal_registry = SignalRegistry()
        return _default_signal_registry


def reset_signal_registry() -> None:
    """Reset the process-wide default signal registry."""
    global _default_signal_registry
    with _registry_lock:
        _default_signal_registry = None

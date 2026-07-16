"""Chronological candle feed with look-ahead protection."""

from __future__ import annotations

from collections.abc import Sequence

from backtesting.exceptions import LookAheadError
from market_data.models.candle import Candle


class ChronologicalCandleFeed:
    """Replay candles in order and block access to future bars."""

    def __init__(self, candles: Sequence[Candle]) -> None:
        ordered = sorted(candles, key=lambda candle: (candle.sequence, candle.timestamp))
        self._candles = tuple(ordered)
        self._current_index = -1
        self._max_accessed_index = -1

    @property
    def total(self) -> int:
        return len(self._candles)

    @property
    def current_index(self) -> int:
        return self._current_index

    @property
    def max_accessed_index(self) -> int:
        return self._max_accessed_index

    def advance_to(self, index: int) -> Candle:
        """Move the replay cursor to ``index`` and return that candle."""
        if index < 0 or index >= len(self._candles):
            msg = f"Invalid candle index: {index}"
            raise LookAheadError(msg)
        self._current_index = index
        self._max_accessed_index = max(self._max_accessed_index, index)
        return self._candles[index]

    def current(self) -> Candle:
        """Return the candle at the current cursor."""
        if self._current_index < 0:
            msg = "Feed cursor is not initialized"
            raise LookAheadError(msg)
        return self._candles[self._current_index]

    def history_window(self) -> tuple[Candle, ...]:
        """Return candles from the start through the current index (inclusive)."""
        if self._current_index < 0:
            return ()
        return self._candles[: self._current_index + 1]

    def peek(self, index: int) -> Candle:
        """Access a candle by index, enforcing no look-ahead beyond current."""
        if index < 0 or index >= len(self._candles):
            msg = f"Invalid candle index: {index}"
            raise LookAheadError(msg)
        if index > self._current_index:
            msg = (
                f"Look-ahead blocked: requested index {index} "
                f"while current index is {self._current_index}"
            )
            raise LookAheadError(msg)
        self._max_accessed_index = max(self._max_accessed_index, index)
        return self._candles[index]

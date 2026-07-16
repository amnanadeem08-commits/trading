"""Deterministic identifier helpers."""

from __future__ import annotations

import hashlib

from backtesting.contracts.request import BacktestRequest


def deterministic_id(prefix: str, *parts: str) -> str:
    digest = hashlib.sha256("|".join(parts).encode()).hexdigest()[:16]
    return f"{prefix}-{digest}"


def resolve_run_id(request: BacktestRequest) -> str:
    if request.run_id is not None and request.run_id.strip():
        return request.run_id.strip()
    first = request.candles[0]
    last = request.candles[-1]
    seed = (
        f"{request.config.seed}|{request.symbol_id}|{request.timeframe}|"
        f"{request.strategy_version}|{len(request.candles)}|"
        f"{first.sequence}|{last.sequence}|{first.timestamp.isoformat()}|"
        f"{last.timestamp.isoformat()}"
    )
    return deterministic_id("btrun", seed)


def trade_id_for_bar(*, run_id: str, bar_index: int, direction: str, timestamp_iso: str) -> str:
    return deterministic_id("bttrade", run_id, str(bar_index), direction, timestamp_iso)

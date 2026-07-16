"""Deterministic JSON serialization for backtest reports."""

from __future__ import annotations

import json
from typing import Any

from backtesting.contracts.report import BacktestReport


def serialize_backtest_report(report: BacktestReport) -> str:
    """Return a deterministic JSON document for the report."""
    payload = report.model_dump(mode="json")
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def deserialize_backtest_report(payload: str | dict[str, Any]) -> BacktestReport:
    """Parse a JSON document into a validated report contract."""
    if isinstance(payload, dict):
        text = json.dumps(payload)
    else:
        text = payload
    return BacktestReport.model_validate_json(text)

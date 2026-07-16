"""Stable portfolio augmentation for the configured crypto universe."""

from __future__ import annotations

from collections.abc import Iterable


def stable_unique_symbols(
    fixed_watchlist: Iterable[str],
    portfolio_symbols: Iterable[str],
) -> tuple[str, ...]:
    """Preserve fixed order, append portfolio symbols, and remove duplicates."""
    merged: list[str] = []
    seen: set[str] = set()
    for raw in (*tuple(fixed_watchlist), *tuple(portfolio_symbols)):
        symbol = raw.strip().upper()
        if not symbol or symbol in seen:
            continue
        seen.add(symbol)
        merged.append(symbol)
    return tuple(merged)

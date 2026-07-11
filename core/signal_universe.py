"""Configured multi-asset universe for the legacy signal scan pipeline.

Loads ``config/signal_universe.yaml`` — not volume rankings or ad-hoc TOP_N caps.
"""

from __future__ import annotations

from collections.abc import Callable
from functools import lru_cache

from config.loader import load_yaml_config
from models.common import ConfigurationError

_DEFAULT_QUOTE = "USDT"
_PSX_SUFFIX = ".KA"


def normalize_crypto_symbol(raw: str, quote: str = _DEFAULT_QUOTE) -> str:
    """Normalize ``BTCUSDT`` or ``BTC/USDT`` to ccxt ``BASE/QUOTE`` form."""
    symbol = (raw or "").strip().upper().replace("-", "/").replace("_", "/")
    if not symbol:
        raise ConfigurationError("crypto symbol entries must be non-empty")
    if "/" in symbol:
        base, _, q = symbol.partition("/")
        if not base or not q:
            raise ConfigurationError(f"invalid crypto symbol: {raw!r}")
        return f"{base}/{q}"
    quote = quote.upper()
    if symbol.endswith(quote) and len(symbol) > len(quote):
        return f"{symbol[: -len(quote)]}/{quote}"
    raise ConfigurationError(
        f"crypto symbol {raw!r} must be BASE/QUOTE or BASE{quote} (e.g. BTCUSDT)"
    )


def normalize_psx_symbol(raw: str) -> str:
    """Normalize ``MARI`` or ``MARI.KA`` to Yahoo ``TICKER.KA`` form."""
    symbol = (raw or "").strip().upper()
    if not symbol:
        raise ConfigurationError("psx symbol entries must be non-empty")
    if "." in symbol:
        return symbol
    return f"{symbol}{_PSX_SUFFIX}"


def normalize_pmex_instrument(raw: str) -> str:
    """Normalize PMEX instrument ids to uppercase underscore form."""
    symbol = (raw or "").strip().upper().replace(" ", "_").replace("-", "_")
    if not symbol:
        raise ConfigurationError("pmex instrument entries must be non-empty")
    return symbol


def _normalize_unique_list(
    raw: object,
    *,
    field_name: str,
    normalize: Callable[[str], str],
) -> list[str]:
    if not isinstance(raw, list) or not raw:
        raise ConfigurationError(f"signal_universe.{field_name} must be a non-empty list")
    normalized: list[str] = []
    seen: set[str] = set()
    for item in raw:
        value = normalize(str(item))
        if value in seen:
            raise ConfigurationError(f"duplicate symbol in signal_universe.{field_name}: {value}")
        seen.add(value)
        normalized.append(value)
    return normalized


@lru_cache(maxsize=1)
def _universe_config() -> dict[str, object]:
    data = load_yaml_config("signal_universe.yaml")
    universe = data.get("signal_universe")
    if not isinstance(universe, dict):
        raise ConfigurationError("signal_universe.yaml must define a signal_universe mapping")
    return universe


def configured_crypto_symbols(*, quote: str = _DEFAULT_QUOTE) -> list[str]:
    """Return configured crypto symbols in ccxt form (full list, no truncation)."""

    def _norm(item: str) -> str:
        return normalize_crypto_symbol(item, quote=quote)

    return _normalize_unique_list(
        _universe_config().get("crypto_symbols"),
        field_name="crypto_symbols",
        normalize=_norm,
    )


def configured_psx_symbols() -> list[str]:
    """Return configured PSX symbols in Yahoo ``.KA`` form (full list)."""
    return _normalize_unique_list(
        _universe_config().get("psx_symbols"),
        field_name="psx_symbols",
        normalize=normalize_psx_symbol,
    )


def configured_pmex_instruments() -> list[str]:
    """Return every configured PMEX instrument (full list — not padded to 20)."""
    return _normalize_unique_list(
        _universe_config().get("pmex_instruments"),
        field_name="pmex_instruments",
        normalize=normalize_pmex_instrument,
    )


def configured_universe_counts() -> dict[str, int]:
    """Return monitored asset counts from configuration (not scan results)."""
    crypto = len(configured_crypto_symbols())
    psx = len(configured_psx_symbols())
    pmex = len(configured_pmex_instruments())
    return {
        "crypto": crypto,
        "psx": psx,
        "pmex": pmex,
        "total": crypto + psx + pmex,
    }


def clear_universe_cache() -> None:
    """Test helper: drop cached YAML parse."""
    _universe_config.cache_clear()

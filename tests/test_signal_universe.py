"""Tests for configured multi-asset signal universe loading."""

from __future__ import annotations

import pytest

from connectors.pmex_connector import get_pmex_instruments
from core import signal_universe as su
from models.common import ConfigurationError


@pytest.fixture(autouse=True)
def _clear_cache():
    su.clear_universe_cache()
    yield
    su.clear_universe_cache()


def test_normalize_crypto_btcusdt() -> None:
    assert su.normalize_crypto_symbol("BTCUSDT") == "BTC/USDT"
    assert su.normalize_crypto_symbol("eth/usdt") == "ETH/USDT"


def test_normalize_psx_bare_ticker() -> None:
    assert su.normalize_psx_symbol("MARI") == "MARI.KA"
    assert su.normalize_psx_symbol("hubc.ka") == "HUBC.KA"


def test_configured_lists_have_twenty_each_and_all_pmex() -> None:
    crypto = su.configured_crypto_symbols()
    psx = su.configured_psx_symbols()
    pmex = su.configured_pmex_instruments()
    assert len(crypto) == 20
    assert len(psx) == 20
    assert len(pmex) == 7
    assert crypto[0] == "BTC/USDT"
    assert "MARI.KA" in psx
    assert "GOLD" in pmex
    assert "NATURAL_GAS" in pmex
    counts = su.configured_universe_counts()
    assert counts == {"crypto": 20, "psx": 20, "pmex": 7, "total": 47}
    assert get_pmex_instruments() == pmex


def test_main_uses_full_configured_universe(monkeypatch: pytest.MonkeyPatch) -> None:
    import main

    class _Exchange:
        rateLimit = 1000  # noqa: N815 — ccxt attribute name

    monkeypatch.setattr(main, "get_exchange", lambda: _Exchange())

    crypto_symbols, _, sleep_s = main.get_symbols_and_fetcher("crypto")
    psx_symbols, _, _ = main.get_symbols_and_fetcher("psx")
    pmex_symbols, _, _ = main.get_symbols_and_fetcher("pmex")

    assert crypto_symbols == su.configured_crypto_symbols()
    assert psx_symbols == su.configured_psx_symbols()
    assert pmex_symbols == su.configured_pmex_instruments()
    assert "USDC/USDT" not in crypto_symbols
    assert len(crypto_symbols) == 20
    assert len(psx_symbols) == 20
    assert len(pmex_symbols) == 7
    assert sleep_s == 1.0


def test_markets_to_run_both_and_all() -> None:
    import main

    assert main.markets_to_run("both") == ["psx", "crypto"]
    assert main.markets_to_run("all") == ["psx", "crypto", "pmex"]
    assert main.markets_to_run("pmex") == ["pmex"]


def test_invalid_crypto_symbol_rejected() -> None:
    with pytest.raises(ConfigurationError, match=r"BASE/QUOTE|BTCUSDT"):
        su.normalize_crypto_symbol("BTC")


def test_invalid_empty_crypto_symbol_rejected() -> None:
    with pytest.raises(ConfigurationError, match="non-empty"):
        su.normalize_crypto_symbol("   ")


def test_invalid_empty_psx_symbol_rejected() -> None:
    with pytest.raises(ConfigurationError, match="non-empty"):
        su.normalize_psx_symbol("")


def test_duplicate_crypto_symbols_rejected() -> None:
    with pytest.raises(ConfigurationError, match=r"duplicate symbol.*crypto_symbols"):
        su._normalize_unique_list(
            ["BTCUSDT", "ETHUSDT", "BTC/USDT"],
            field_name="crypto_symbols",
            normalize=su.normalize_crypto_symbol,
        )


def test_duplicate_psx_symbols_rejected() -> None:
    with pytest.raises(ConfigurationError, match=r"duplicate symbol.*psx_symbols"):
        su._normalize_unique_list(
            ["MARI", "OGDC", "mari.ka"],
            field_name="psx_symbols",
            normalize=su.normalize_psx_symbol,
        )


def test_empty_list_rejected() -> None:
    with pytest.raises(ConfigurationError, match="non-empty list"):
        su._normalize_unique_list(
            [],
            field_name="crypto_symbols",
            normalize=su.normalize_crypto_symbol,
        )


def test_no_top_n_in_legacy_config() -> None:
    import legacy_config

    assert not hasattr(legacy_config, "TOP_N")

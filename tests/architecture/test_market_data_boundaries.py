"""Architecture tests for market data framework boundaries."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from architecture.dependency_rules import FORBIDDEN_IMPORT_PAIRS

MARKET_DATA_MODULE_ROOT = Path("market_data")

FORBIDDEN_TERMS = (
    "http",
    "websocket",
    "requests",
    "aiohttp",
    "urllib",
    "socket",
    "pmex",
    "crypto",
    "binance",
    "broker",
    "exchange",
)


def _iter_market_data_source_files() -> list[Path]:
    return sorted(MARKET_DATA_MODULE_ROOT.rglob("*.py"))


@pytest.mark.architecture
def test_market_data_modules_exist(validator) -> None:
    source_files = validator._load_source_files()
    module_names = {item.relative_path for item in source_files}
    assert "market_data/models/market_record.py" in module_names
    assert "market_data/schema/normalization.py" in module_names
    assert "market_data/stream/stream_buffer.py" in module_names
    assert "market_data/registry/market_registry.py" in module_names


@pytest.mark.architecture
def test_market_data_modules_do_not_import_forbidden_packages() -> None:
    forbidden = FORBIDDEN_IMPORT_PAIRS["market_data"]
    for path in _iter_market_data_source_files():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root = alias.name.split(".")[0]
                    assert root not in forbidden, f"{path} imports {root}"
            elif isinstance(node, ast.ImportFrom) and node.module:
                root = node.module.split(".")[0]
                assert root not in forbidden, f"{path} imports {root}"


@pytest.mark.architecture
def test_market_data_modules_avoid_networking_terms() -> None:
    for path in _iter_market_data_source_files():
        content = path.read_text(encoding="utf-8").lower()
        for term in FORBIDDEN_TERMS:
            assert term not in content, f"{path} contains forbidden term '{term}'"


@pytest.mark.architecture
def test_market_data_public_exports() -> None:
    from market_data import MarketDataRegistry, MarketRecord, StreamBuffer

    assert MarketDataRegistry.__name__ == "MarketDataRegistry"
    assert MarketRecord.__name__ == "MarketRecord"
    assert StreamBuffer.__name__ == "StreamBuffer"


@pytest.mark.architecture
def test_historical_does_not_import_market_data(architecture_report) -> None:
    violations = [
        violation
        for violation in architecture_report.violations
        if violation.file_path.startswith("historical/") and "market_data" in violation.detail
    ]
    assert violations == []

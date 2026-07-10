"""Architecture tests for historical repository boundaries."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from architecture.dependency_rules import PIPELINE_PACKAGES, PipelineLayer

HISTORICAL_MODULE_ROOT = Path("historical")

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
    "sqlalchemy",
    "sqlite3",
    "psycopg",
)


def _iter_historical_source_files() -> list[Path]:
    return sorted(HISTORICAL_MODULE_ROOT.rglob("*.py"))


@pytest.mark.architecture
def test_historical_package_exists(validator) -> None:
    source_files = validator._load_source_files()
    module_names = {item.relative_path for item in source_files}
    assert "historical/storage/repository.py" in module_names
    assert "historical/replay/replay_engine.py" in module_names
    assert "historical/query/query_engine.py" in module_names


@pytest.mark.architecture
def test_historical_is_lowest_pipeline_layer() -> None:
    assert PIPELINE_PACKAGES["historical"] == PipelineLayer.HISTORICAL
    historical_layer = PIPELINE_PACKAGES["historical"]
    for package, layer in PIPELINE_PACKAGES.items():
        if package == "historical":
            continue
        assert layer > historical_layer


@pytest.mark.architecture
def test_historical_modules_avoid_networking_terms() -> None:
    for path in _iter_historical_source_files():
        content = path.read_text(encoding="utf-8").lower()
        for term in FORBIDDEN_TERMS:
            assert term not in content, f"{path} contains forbidden term '{term}'"


@pytest.mark.architecture
def test_historical_does_not_import_connectors() -> None:
    for path in _iter_historical_source_files():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root = alias.name.split(".")[0]
                    assert root != "connectors", f"{path} imports connectors"
            elif isinstance(node, ast.ImportFrom) and node.module:
                root = node.module.split(".")[0]
                assert root != "connectors", f"{path} imports connectors"


@pytest.mark.architecture
def test_historical_public_exports() -> None:
    from historical import HistoricalRegistry, ReplayEngine, Repository

    assert Repository.__name__ == "Repository"
    assert ReplayEngine.__name__ == "ReplayEngine"
    assert HistoricalRegistry.__name__ == "HistoricalRegistry"

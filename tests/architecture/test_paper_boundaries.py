"""Architecture tests for paper adapter boundaries."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from architecture.dependency_rules import CONNECTOR_FORBIDDEN_IMPORTS

PAPER_MODULE_ROOTS = (
    "connectors/adapters/paper",
    "connectors/simulation",
    "connectors/validation/paper_validator.py",
)

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
)


def _iter_paper_source_files() -> list[Path]:
    root = Path("connectors")
    files: list[Path] = []
    for relative in PAPER_MODULE_ROOTS:
        path = root / relative
        if path.is_file():
            files.append(path)
        elif path.is_dir():
            files.extend(sorted(path.rglob("*.py")))
    return files


@pytest.mark.architecture
def test_paper_modules_exist(validator) -> None:
    source_files = validator._load_source_files()
    module_names = {item.relative_path for item in source_files}
    assert "connectors/adapters/paper/paper_adapter.py" in module_names
    assert "connectors/simulation/simulation_engine.py" in module_names
    assert "connectors/validation/paper_validator.py" in module_names


@pytest.mark.architecture
def test_paper_modules_do_not_import_forbidden_packages() -> None:
    for path in _iter_paper_source_files():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root = alias.name.split(".")[0]
                    assert root not in CONNECTOR_FORBIDDEN_IMPORTS, f"{path} imports {root}"
            elif isinstance(node, ast.ImportFrom) and node.module:
                root = node.module.split(".")[0]
                assert root not in CONNECTOR_FORBIDDEN_IMPORTS, f"{path} imports {root}"


@pytest.mark.architecture
def test_paper_modules_avoid_networking_terms() -> None:
    for path in _iter_paper_source_files():
        content = path.read_text(encoding="utf-8").lower()
        for term in FORBIDDEN_TERMS:
            assert term not in content, f"{path} contains forbidden term '{term}'"


@pytest.mark.architecture
def test_execution_does_not_import_paper_adapter(architecture_report) -> None:
    violations = [
        violation
        for violation in architecture_report.violations
        if violation.file_path.startswith("execution/") and "connectors" in violation.detail
    ]
    assert violations == []


@pytest.mark.architecture
def test_paper_adapter_public_exports() -> None:
    from connectors import PaperExecutionAdapter, SimulationEngine

    assert PaperExecutionAdapter.__name__ == "PaperExecutionAdapter"
    assert SimulationEngine.__name__ == "SimulationEngine"

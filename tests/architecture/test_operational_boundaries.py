"""Architecture tests for operational package boundaries."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]

OPERATIONAL_PACKAGES = (
    "health",
    "metrics",
    "platform_logging",
    "security",
    "notifications",
    "monitoring",
)

FORBIDDEN_IMPORTS = {
    "connectors",
    "research",
    "ml",
    "ai",
    "agents",
    "decision",
    "core",
    "services",
}


def _python_files(package: str) -> list[Path]:
    package_dir = PROJECT_ROOT / package
    if not package_dir.exists():
        return []
    return sorted(path for path in package_dir.rglob("*.py"))


def _imported_roots(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".")[0])
    return imports


@pytest.mark.architecture
def test_operational_packages_avoid_forbidden_dependencies() -> None:
    violations: list[str] = []
    for package in OPERATIONAL_PACKAGES:
        for path in _python_files(package):
            blocked = sorted(_imported_roots(path).intersection(FORBIDDEN_IMPORTS))
            if blocked:
                violations.append(f"{path.relative_to(PROJECT_ROOT)} -> {blocked}")
    assert violations == []


@pytest.mark.architecture
def test_operational_packages_remain_independent_of_research() -> None:
    violations: list[str] = []
    for package in OPERATIONAL_PACKAGES:
        for path in _python_files(package):
            if "research" in _imported_roots(path):
                violations.append(str(path.relative_to(PROJECT_ROOT)))
    assert violations == []


@pytest.mark.architecture
def test_monitoring_only_composes_health_and_metrics() -> None:
    allowed = {
        "monitoring",
        "health",
        "metrics",
        "config",
        "models",
        "__future__",
        "typing",
    }
    violations: list[str] = []
    for path in _python_files("monitoring"):
        blocked = sorted(_imported_roots(path) - allowed)
        if blocked:
            violations.append(f"{path.relative_to(PROJECT_ROOT)} -> {blocked}")
    assert violations == []

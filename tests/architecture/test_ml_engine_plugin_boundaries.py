"""Architecture tests for ML engine plugin boundaries."""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

from architecture.dependency_rules import FORBIDDEN_IMPORT_PAIRS, RULE_IDS

ML_ENGINE_PLUGINS_MODULE_ROOT = Path("ml_engine_plugins")

FORBIDDEN_TERMS = (
    "http",
    "websocket",
    "aiohttp",
    "urllib",
    "socket",
    "pmex",
    "crypto",
    "binance",
    "broker",
    "exchange",
)

TECHNICAL_TERM_PATTERNS = (
    re.compile(r"\btensorflow\b"),
    re.compile(r"\bpytorch\b"),
    re.compile(r"\bsklearn\b"),
    re.compile(r"\bscikit-learn\b"),
    re.compile(r"\bonnx\b"),
    re.compile(r"\bxgboost\b"),
    re.compile(r"\blightgbm\b"),
    re.compile(r"\bcatboost\b"),
    re.compile(r"\bpredict\b"),
    re.compile(r"\bportfolio\b"),
)


def _iter_ml_engine_plugins_source_files() -> list[Path]:
    return sorted(ML_ENGINE_PLUGINS_MODULE_ROOT.rglob("*.py"))


@pytest.mark.architecture
def test_ml_engine_plugins_modules_exist(validator) -> None:
    source_files = validator._load_source_files()
    module_names = {item.relative_path for item in source_files}
    assert "ml_engine_plugins/ml_runtime_bridge.py" in module_names
    assert "ml_engine_plugins/plugin.py" in module_names
    assert "ml_engine_plugins/plugin_registry.py" in module_names


@pytest.mark.architecture
def test_ml_engine_plugins_do_not_import_forbidden_packages() -> None:
    forbidden = FORBIDDEN_IMPORT_PAIRS["ml_engine_plugins"]
    for path in _iter_ml_engine_plugins_source_files():
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
def test_ml_engine_plugins_avoid_forbidden_terms() -> None:
    for path in _iter_ml_engine_plugins_source_files():
        content = path.read_text(encoding="utf-8").lower()
        for term in FORBIDDEN_TERMS:
            assert term not in content, f"{path} contains forbidden term '{term}'"
        for pattern in TECHNICAL_TERM_PATTERNS:
            assert (
                pattern.search(content) is None
            ), f"{path} contains forbidden pattern '{pattern.pattern}'"


@pytest.mark.architecture
def test_ml_engine_plugins_public_exports() -> None:
    from ml_engine_plugins import MLPlugin, MLRuntimePluginBridge, build_plugin_bridge

    assert MLPlugin is not None
    assert MLRuntimePluginBridge is not None
    assert callable(build_plugin_bridge)


@pytest.mark.architecture
def test_ml_runtime_does_not_import_ml_engine_plugins(architecture_report) -> None:
    violations = [
        violation
        for violation in architecture_report.violations
        if violation.file_path.startswith("ml_runtime/") and "ml_engine_plugins" in violation.detail
    ]
    assert violations == []


@pytest.mark.architecture
def test_ml_engine_plugins_boundary_rule_registered() -> None:
    assert "ml_engine_plugins_boundary" in RULE_IDS

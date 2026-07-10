"""Architecture tests for framework adapter boundaries."""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

from architecture.dependency_rules import FORBIDDEN_IMPORT_PAIRS, RULE_IDS

FRAMEWORK_ADAPTERS_MODULE_ROOT = Path("framework_adapters")

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

TERM_SCAN_EXCLUDED_FILES = frozenset(
    {
        "framework_adapters/contracts/engine_type.py",
    }
)


def _iter_framework_adapters_source_files() -> list[Path]:
    return sorted(FRAMEWORK_ADAPTERS_MODULE_ROOT.rglob("*.py"))


@pytest.mark.architecture
def test_framework_adapters_modules_exist(validator) -> None:
    source_files = validator._load_source_files()
    module_names = {item.relative_path for item in source_files}
    assert "framework_adapters/integration/ml_engine_bridge.py" in module_names
    assert "framework_adapters/adapters/stub_framework_adapter.py" in module_names
    assert "framework_adapters/contracts/framework_adapter.py" in module_names
    assert "framework_adapters/registry/adapter_registry.py" in module_names
    assert "framework_adapters/runtime/adapter_runtime.py" in module_names


@pytest.mark.architecture
def test_framework_adapters_do_not_import_forbidden_packages() -> None:
    forbidden = FORBIDDEN_IMPORT_PAIRS["framework_adapters"]
    for path in _iter_framework_adapters_source_files():
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
def test_framework_adapters_avoid_forbidden_terms() -> None:
    for path in _iter_framework_adapters_source_files():
        relative = path.as_posix()
        if relative in TERM_SCAN_EXCLUDED_FILES:
            continue
        content = path.read_text(encoding="utf-8").lower()
        for term in FORBIDDEN_TERMS:
            assert term not in content, f"{path} contains forbidden term '{term}'"
        for pattern in TECHNICAL_TERM_PATTERNS:
            assert (
                pattern.search(content) is None
            ), f"{path} contains forbidden pattern '{pattern.pattern}'"


@pytest.mark.architecture
def test_framework_adapters_public_exports() -> None:
    from framework_adapters import FrameworkAdapter, MLEngineAdapterBridge, build_adapter_bridge

    assert FrameworkAdapter is not None
    assert MLEngineAdapterBridge is not None
    assert callable(build_adapter_bridge)


@pytest.mark.architecture
def test_ml_runtime_does_not_import_framework_adapters(architecture_report) -> None:
    violations = [
        violation
        for violation in architecture_report.violations
        if violation.file_path.startswith("ml_runtime/")
        and "framework_adapters" in violation.detail
    ]
    assert violations == []


@pytest.mark.architecture
def test_ml_engine_plugins_does_not_import_framework_adapters(architecture_report) -> None:
    violations = [
        violation
        for violation in architecture_report.violations
        if violation.file_path.startswith("ml_engine_plugins/")
        and "framework_adapters" in violation.detail
    ]
    assert violations == []


@pytest.mark.architecture
def test_framework_adapters_boundary_rule_registered() -> None:
    assert "framework_adapters_boundary" in RULE_IDS


@pytest.mark.architecture
def test_framework_adapters_sits_between_ml_engine_plugins_and_ml() -> None:
    from architecture.dependency_rules import PIPELINE_PACKAGES

    plugins_layer = PIPELINE_PACKAGES["ml_engine_plugins"]
    adapters_layer = PIPELINE_PACKAGES["framework_adapters"]
    ml_layer = PIPELINE_PACKAGES["ml"]
    assert adapters_layer > plugins_layer
    assert ml_layer > adapters_layer

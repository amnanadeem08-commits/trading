"""Architecture tests for model registry boundaries."""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

from architecture.dependency_rules import FORBIDDEN_IMPORT_PAIRS, RULE_IDS

MODEL_REGISTRY_MODULE_ROOT = Path("model_registry")

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
    re.compile(r"\bxgboost\b"),
    re.compile(r"\blightgbm\b"),
    re.compile(r"\bcatboost\b"),
    re.compile(r"\bopenai\b"),
    re.compile(r"\bpredict\b"),
    re.compile(r"\binference\b"),
    re.compile(r"\bportfolio\b"),
)


def _iter_model_registry_source_files() -> list[Path]:
    return sorted(MODEL_REGISTRY_MODULE_ROOT.rglob("*.py"))


@pytest.mark.architecture
def test_model_registry_modules_exist(validator) -> None:
    source_files = validator._load_source_files()
    module_names = {item.relative_path for item in source_files}
    assert "model_registry/registry/model_registry.py" in module_names
    assert "model_registry/integration/training_pipeline_bridge.py" in module_names
    assert "model_registry/lineage/lineage_graph.py" in module_names


@pytest.mark.architecture
def test_model_registry_modules_do_not_import_forbidden_packages() -> None:
    forbidden = FORBIDDEN_IMPORT_PAIRS["model_registry"]
    for path in _iter_model_registry_source_files():
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
def test_model_registry_modules_avoid_forbidden_terms() -> None:
    for path in _iter_model_registry_source_files():
        content = path.read_text(encoding="utf-8").lower()
        for term in FORBIDDEN_TERMS:
            assert term not in content, f"{path} contains forbidden term '{term}'"
        for pattern in TECHNICAL_TERM_PATTERNS:
            assert (
                pattern.search(content) is None
            ), f"{path} contains forbidden pattern '{pattern.pattern}'"


@pytest.mark.architecture
def test_model_registry_public_exports() -> None:
    from model_registry import (
        LineageGraph,
        ModelCatalog,
        ModelRegistry,
        ModelRegistryRuntime,
        RegisteredModel,
        build_model_registry_runtime,
    )

    assert ModelRegistry is not None
    assert RegisteredModel is not None
    assert ModelCatalog is not None
    assert LineageGraph is not None
    assert ModelRegistryRuntime is not None
    assert callable(build_model_registry_runtime)


@pytest.mark.architecture
def test_training_pipeline_does_not_import_model_registry(architecture_report) -> None:
    violations = [
        violation
        for violation in architecture_report.violations
        if violation.file_path.startswith("training_pipeline/")
        and "model_registry" in violation.detail
    ]
    assert violations == []


@pytest.mark.architecture
def test_model_registry_boundary_rule_registered() -> None:
    assert "model_registry_boundary" in RULE_IDS

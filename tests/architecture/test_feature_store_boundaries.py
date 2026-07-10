"""Architecture tests for feature store boundaries."""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

from architecture.dependency_rules import FORBIDDEN_IMPORT_PAIRS, RULE_IDS

FEATURE_STORE_MODULE_ROOT = Path("feature_store")

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

TECHNICAL_TERM_PATTERNS = (
    re.compile(r"\btensorflow\b"),
    re.compile(r"\bpytorch\b"),
    re.compile(r"\bsklearn\b"),
    re.compile(r"\bscikit-learn\b"),
    re.compile(r"\bpredict\b"),
    re.compile(r"\binference\b"),
    re.compile(r"\bportfolio\b"),
)


def _iter_feature_store_source_files() -> list[Path]:
    return sorted(FEATURE_STORE_MODULE_ROOT.rglob("*.py"))


@pytest.mark.architecture
def test_feature_store_modules_exist(validator) -> None:
    source_files = validator._load_source_files()
    module_names = {item.relative_path for item in source_files}
    assert "feature_store/storage/feature_store.py" in module_names
    assert "feature_store/integration/feature_engineering_bridge.py" in module_names
    assert "feature_store/registry/dataset_registry.py" in module_names


@pytest.mark.architecture
def test_feature_store_modules_do_not_import_forbidden_packages() -> None:
    forbidden = FORBIDDEN_IMPORT_PAIRS["feature_store"]
    for path in _iter_feature_store_source_files():
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
def test_feature_store_modules_avoid_forbidden_terms() -> None:
    for path in _iter_feature_store_source_files():
        content = path.read_text(encoding="utf-8").lower()
        for term in FORBIDDEN_TERMS:
            assert term not in content, f"{path} contains forbidden term '{term}'"
        for pattern in TECHNICAL_TERM_PATTERNS:
            assert (
                pattern.search(content) is None
            ), f"{path} contains forbidden pattern '{pattern.pattern}'"


@pytest.mark.architecture
def test_feature_store_public_exports() -> None:
    from feature_store import FeatureRecord, FeatureStore, ingest_feature_set

    assert FeatureStore.__name__ == "FeatureStore"
    assert FeatureRecord.__name__ == "FeatureRecord"
    assert callable(ingest_feature_set)


@pytest.mark.architecture
def test_feature_engineering_does_not_import_feature_store(architecture_report) -> None:
    violations = [
        violation
        for violation in architecture_report.violations
        if violation.file_path.startswith("feature_engineering/")
        and "feature_store" in violation.detail
    ]
    assert violations == []


@pytest.mark.architecture
def test_feature_store_boundary_rule_registered() -> None:
    assert "feature_store_boundary" in RULE_IDS

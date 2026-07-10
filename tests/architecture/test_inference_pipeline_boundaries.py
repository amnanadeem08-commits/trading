"""Architecture tests for inference pipeline boundaries."""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

from architecture.dependency_rules import FORBIDDEN_IMPORT_PAIRS, RULE_IDS

INFERENCE_PIPELINE_MODULE_ROOT = Path("inference_pipeline")

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
    re.compile(r"\bpredict\b"),
    re.compile(r"\binference engine\b"),
    re.compile(r"\bportfolio\b"),
)


def _iter_inference_pipeline_source_files() -> list[Path]:
    return sorted(INFERENCE_PIPELINE_MODULE_ROOT.rglob("*.py"))


@pytest.mark.architecture
def test_inference_pipeline_modules_exist(validator) -> None:
    source_files = validator._load_source_files()
    module_names = {item.relative_path for item in source_files}
    assert "inference_pipeline/runtime/inference_runtime.py" in module_names
    assert "inference_pipeline/integration/model_registry_bridge.py" in module_names
    assert "inference_pipeline/runtime/model_loader.py" in module_names


@pytest.mark.architecture
def test_inference_pipeline_modules_do_not_import_forbidden_packages() -> None:
    forbidden = FORBIDDEN_IMPORT_PAIRS["inference_pipeline"]
    for path in _iter_inference_pipeline_source_files():
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
def test_inference_pipeline_modules_avoid_forbidden_terms() -> None:
    for path in _iter_inference_pipeline_source_files():
        content = path.read_text(encoding="utf-8").lower()
        for term in FORBIDDEN_TERMS:
            assert term not in content, f"{path} contains forbidden term '{term}'"
        for pattern in TECHNICAL_TERM_PATTERNS:
            assert (
                pattern.search(content) is None
            ), f"{path} contains forbidden pattern '{pattern.pattern}'"


@pytest.mark.architecture
def test_inference_pipeline_public_exports() -> None:
    from inference_pipeline import (
        InferenceRequest,
        InferenceRuntime,
        InferenceScheduler,
        ModelLoader,
        build_inference_runtime,
    )

    assert InferenceRequest is not None
    assert InferenceRuntime is not None
    assert InferenceScheduler is not None
    assert ModelLoader is not None
    assert callable(build_inference_runtime)


@pytest.mark.architecture
def test_model_registry_does_not_import_inference_pipeline(architecture_report) -> None:
    violations = [
        violation
        for violation in architecture_report.violations
        if violation.file_path.startswith("model_registry/")
        and "inference_pipeline" in violation.detail
    ]
    assert violations == []


@pytest.mark.architecture
def test_inference_pipeline_boundary_rule_registered() -> None:
    assert "inference_pipeline_boundary" in RULE_IDS

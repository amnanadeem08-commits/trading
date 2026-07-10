"""Architecture tests for core layer boundaries."""

from __future__ import annotations

import pytest

from architecture.dependency_rules import FORBIDDEN_IMPORT_PAIRS, PIPELINE_PACKAGES, RULE_IDS


@pytest.mark.architecture
def test_core_package_is_in_pipeline_layers() -> None:
    assert "core" in PIPELINE_PACKAGES


@pytest.mark.architecture
def test_core_forbidden_imports_are_defined() -> None:
    forbidden = FORBIDDEN_IMPORT_PAIRS["core"]
    assert "connectors" in forbidden
    assert "ai" in forbidden
    assert "ml" in forbidden
    assert "decision" in forbidden
    assert "risk" in forbidden
    assert "execution" in forbidden
    assert "api" in forbidden
    assert "dashboard" in forbidden
    assert "research" in forbidden


@pytest.mark.architecture
def test_core_boundary_rule_id() -> None:
    assert RULE_IDS["core_boundary"] == "R11"


@pytest.mark.architecture
def test_core_does_not_import_connectors(architecture_report) -> None:
    violations = [
        violation
        for violation in architecture_report.violations
        if violation.rule_name in {"forbidden_import", "core_boundary"}
        and "core must not import connectors" in violation.detail
        and violation.file_path.startswith("core/")
    ]
    assert violations == []


@pytest.mark.architecture
def test_core_does_not_import_ml_or_ai(architecture_report) -> None:
    violations = [
        violation
        for violation in architecture_report.violations
        if violation.rule_name in {"forbidden_import", "core_boundary"}
        and violation.file_path.startswith("core/")
        and (
            "core must not import ml" in violation.detail
            or "core must not import ai" in violation.detail
        )
    ]
    assert violations == []


@pytest.mark.architecture
def test_core_package_exists(validator) -> None:
    source_files = validator._load_source_files()
    core_files = [item for item in source_files if item.package == "core"]
    assert core_files
    module_names = {item.relative_path for item in core_files}
    assert "core/__init__.py" in module_names
    assert "core/runtime.py" in module_names
    assert "core/context/core_context.py" in module_names

"""Architecture tests for pipeline layer boundaries."""

from __future__ import annotations

import pytest

from architecture.dependency_rules import FORBIDDEN_IMPORT_PAIRS, ORCHESTRATION_PACKAGES


@pytest.mark.architecture
def test_pipeline_packages_are_defined() -> None:
    assert "pipeline" in ORCHESTRATION_PACKAGES


@pytest.mark.architecture
def test_pipeline_forbidden_imports_are_defined() -> None:
    forbidden = FORBIDDEN_IMPORT_PAIRS["pipeline"]
    assert "connectors" in forbidden
    assert "ml" in forbidden
    assert "ai" in forbidden
    assert "risk" in forbidden
    assert "execution" in forbidden
    assert "api" in forbidden
    assert "dashboard" in forbidden


@pytest.mark.architecture
def test_pipeline_does_not_import_connectors(architecture_report) -> None:
    violations = [
        violation
        for violation in architecture_report.violations
        if violation.rule_name in {"forbidden_import", "pipeline_boundary"}
        and "pipeline must not import connectors" in violation.detail
        and violation.file_path.startswith("pipeline/")
    ]
    assert violations == []


@pytest.mark.architecture
def test_pipeline_does_not_import_ml_or_ai(architecture_report) -> None:
    violations = [
        violation
        for violation in architecture_report.violations
        if violation.rule_name in {"forbidden_import", "pipeline_boundary"}
        and violation.file_path.startswith("pipeline/")
        and (
            "pipeline must not import ml" in violation.detail
            or "pipeline must not import ai" in violation.detail
        )
    ]
    assert violations == []


@pytest.mark.architecture
def test_pipeline_has_no_market_branching(architecture_report) -> None:
    violations = [
        violation
        for violation in architecture_report.violations
        if violation.rule_name == "pipeline_boundary"
        and "market-specific branching" in violation.detail
    ]
    assert violations == []


@pytest.mark.architecture
def test_pipeline_package_exists(validator) -> None:
    source_files = validator._load_source_files()
    pipeline_files = [item for item in source_files if item.package in ORCHESTRATION_PACKAGES]
    assert pipeline_files
    module_names = {item.relative_path for item in pipeline_files}
    assert "pipeline/__init__.py" in module_names
    assert "pipeline/executor.py" in module_names
    assert "pipeline/stage.py" in module_names

"""Architecture tests for data layer boundaries."""

from __future__ import annotations

import pytest

from architecture.dependency_rules import FORBIDDEN_IMPORT_PAIRS, PIPELINE_PACKAGES, RULE_IDS


@pytest.mark.architecture
def test_data_package_is_in_pipeline_layers() -> None:
    assert "data" in PIPELINE_PACKAGES


@pytest.mark.architecture
def test_data_forbidden_imports_are_defined() -> None:
    forbidden = FORBIDDEN_IMPORT_PAIRS["data"]
    assert "connectors" in forbidden
    assert "core" in forbidden
    assert "ml" in forbidden
    assert "ai" in forbidden
    assert "decision" in forbidden
    assert "risk" in forbidden
    assert "execution" in forbidden
    assert "api" in forbidden
    assert "dashboard" in forbidden
    assert "research" in forbidden


@pytest.mark.architecture
def test_data_boundary_rule_id() -> None:
    assert RULE_IDS["data_boundary"] == "R11"


@pytest.mark.architecture
def test_data_does_not_import_connectors(architecture_report) -> None:
    violations = [
        violation
        for violation in architecture_report.violations
        if violation.rule_name in {"forbidden_import", "data_boundary"}
        and "data must not import connectors" in violation.detail
        and violation.file_path.startswith("data/")
    ]
    assert violations == []


@pytest.mark.architecture
def test_data_does_not_import_core_or_ml(architecture_report) -> None:
    violations = [
        violation
        for violation in architecture_report.violations
        if violation.rule_name in {"forbidden_import", "data_boundary"}
        and violation.file_path.startswith("data/")
        and (
            "data must not import core" in violation.detail
            or "data must not import ml" in violation.detail
        )
    ]
    assert violations == []


@pytest.mark.architecture
def test_data_has_no_market_branching(architecture_report) -> None:
    violations = [
        violation
        for violation in architecture_report.violations
        if violation.rule_name == "data_boundary"
        and "market-specific branching" in violation.detail
    ]
    assert violations == []


@pytest.mark.architecture
def test_data_package_exists(validator) -> None:
    source_files = validator._load_source_files()
    data_files = [item for item in source_files if item.package == "data"]
    assert data_files
    module_names = {item.relative_path for item in data_files}
    assert "data/__init__.py" in module_names
    assert "data/registry.py" in module_names
    assert "data/dataset.py" in module_names

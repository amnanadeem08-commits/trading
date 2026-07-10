"""Architecture tests for execution layer boundaries."""

from __future__ import annotations

import pytest

from architecture.dependency_rules import FORBIDDEN_IMPORT_PAIRS, PIPELINE_PACKAGES, RULE_IDS


@pytest.mark.architecture
def test_execution_package_is_in_pipeline_layers() -> None:
    assert "execution" in PIPELINE_PACKAGES


@pytest.mark.architecture
def test_execution_forbidden_imports_are_defined() -> None:
    forbidden = FORBIDDEN_IMPORT_PAIRS["execution"]
    assert "connectors" in forbidden
    assert "api" in forbidden
    assert "dashboard" in forbidden
    assert "research" in forbidden


@pytest.mark.architecture
def test_execution_boundary_rule_id() -> None:
    assert RULE_IDS["execution_boundary"] == "R11"


@pytest.mark.architecture
def test_execution_does_not_import_connectors(architecture_report) -> None:
    violations = [
        violation
        for violation in architecture_report.violations
        if violation.rule_name in {"forbidden_import", "execution_boundary"}
        and violation.file_path.startswith("execution/")
        and "execution must not import connectors" in violation.detail
    ]
    assert violations == []


@pytest.mark.architecture
def test_execution_package_exists(validator) -> None:
    source_files = validator._load_source_files()
    execution_files = [item for item in source_files if item.package == "execution"]
    assert execution_files
    module_names = {item.relative_path for item in execution_files}
    assert "execution/__init__.py" in module_names
    assert "execution/orchestration/execution_orchestrator.py" in module_names
    assert "execution/lifecycle/execution_lifecycle_manager.py" in module_names

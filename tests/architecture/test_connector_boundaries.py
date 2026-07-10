"""Architecture tests for connector framework boundaries."""

from __future__ import annotations

import pytest

from architecture.dependency_rules import (
    CONNECTOR_FORBIDDEN_IMPORTS,
    CONNECTOR_IMPORT_FORBIDDEN_SOURCES,
    FORBIDDEN_IMPORT_PAIRS,
    PIPELINE_PACKAGES,
    RULE_IDS,
)


@pytest.mark.architecture
def test_connectors_package_is_in_pipeline_layers() -> None:
    assert "connectors" in PIPELINE_PACKAGES


@pytest.mark.architecture
def test_connectors_forbidden_imports_are_defined() -> None:
    forbidden = FORBIDDEN_IMPORT_PAIRS["connectors"]
    assert "dashboard" in forbidden
    assert "api" in forbidden
    assert "research" in forbidden
    assert "services" in forbidden


@pytest.mark.architecture
def test_connector_boundary_rule_id() -> None:
    assert RULE_IDS["connector_boundary"] == "R10"


@pytest.mark.architecture
def test_connectors_may_import_execution(architecture_report) -> None:
    violations = [
        violation
        for violation in architecture_report.violations
        if violation.rule_name == "connector_boundary"
        and violation.file_path.startswith("connectors/")
        and "connectors must not import execution" in violation.detail
    ]
    assert violations == []


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
def test_connector_framework_package_exists(validator) -> None:
    source_files = validator._load_source_files()
    connector_files = [item for item in source_files if item.package == "connectors"]
    assert connector_files
    module_names = {item.relative_path for item in connector_files}
    assert "connectors/adapters/execution_adapter.py" in module_names
    assert "connectors/dispatch/dispatch_bridge.py" in module_names
    assert "connectors/orchestration/connector_orchestrator.py" in module_names


@pytest.mark.architecture
def test_connector_forbidden_imports_allow_execution_layer() -> None:
    assert "execution" not in CONNECTOR_FORBIDDEN_IMPORTS
    assert "core" not in CONNECTOR_FORBIDDEN_IMPORTS


@pytest.mark.architecture
def test_foundation_layers_do_not_import_connectors(architecture_report) -> None:
    violations = [
        violation
        for violation in architecture_report.violations
        if violation.rule_name == "connector_boundary"
        and "must not import connectors" in violation.detail
        and not violation.file_path.startswith("connectors/")
    ]
    assert violations == []


@pytest.mark.architecture
def test_registry_has_no_market_branching(architecture_report) -> None:
    violations = [
        violation
        for violation in architecture_report.violations
        if violation.rule_name == "connector_boundary"
        and "registry must not contain market-specific branching" in violation.detail
    ]
    assert violations == []


@pytest.mark.architecture
def test_connector_import_forbidden_sources_include_models_and_config() -> None:
    assert "models" in CONNECTOR_IMPORT_FORBIDDEN_SOURCES
    assert "config" in CONNECTOR_IMPORT_FORBIDDEN_SOURCES

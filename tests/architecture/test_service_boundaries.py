"""Architecture tests for service layer boundaries."""

from __future__ import annotations

import pytest

from architecture.dependency_rules import SERVICE_PACKAGES


@pytest.mark.architecture
def test_service_packages_are_defined() -> None:
    assert frozenset({"services"}) == SERVICE_PACKAGES


@pytest.mark.architecture
def test_services_do_not_import_connectors_directly(architecture_report) -> None:
    violations = [
        violation
        for violation in architecture_report.violations
        if violation.rule_name == "service_boundary" and "import connectors" in violation.detail
    ]
    assert violations == []


@pytest.mark.architecture
def test_services_have_no_market_branching(architecture_report) -> None:
    violations = [
        violation
        for violation in architecture_report.violations
        if violation.rule_name == "service_boundary"
        and "market-specific branching" in violation.detail
    ]
    assert violations == []


@pytest.mark.architecture
def test_services_package_exists(validator) -> None:
    source_files = validator._load_source_files()
    service_files = [item for item in source_files if item.package in SERVICE_PACKAGES]
    assert service_files
    module_names = {item.relative_path for item in service_files}
    assert "services/__init__.py" in module_names
    assert "services/service.py" in module_names
    assert "services/registry.py" in module_names

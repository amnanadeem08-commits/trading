"""Architecture tests for pipeline dependency direction."""

from __future__ import annotations

import pytest

from architecture.dependency_rules import PIPELINE_PACKAGES, PipelineLayer
from tests.architecture.conftest import PROJECT_ROOT


@pytest.mark.architecture
def test_pipeline_layer_order_is_frozen() -> None:
    assert [layer.name for layer in PipelineLayer] == [
        "HISTORICAL",
        "CONNECTORS",
        "DATA",
        "CORE",
        "ML",
        "AI",
        "AGENTS",
        "DECISION",
        "RISK",
        "EXECUTION",
    ]
    assert PIPELINE_PACKAGES["historical"] == PipelineLayer.HISTORICAL
    assert PIPELINE_PACKAGES["connectors"] == PipelineLayer.CONNECTORS
    assert PIPELINE_PACKAGES["execution"] == PipelineLayer.EXECUTION


@pytest.mark.architecture
def test_no_reverse_pipeline_imports(architecture_report) -> None:
    violations = [
        violation
        for violation in architecture_report.violations
        if violation.rule_name == "dependency_direction"
    ]
    assert violations == []


@pytest.mark.architecture
def test_foundation_packages_do_not_import_pipeline_layers(validator) -> None:
    source_files = validator._load_source_files()
    violations = validator._validate_dependency_direction(source_files)
    foundation_violations = [
        violation for violation in violations if violation.file_path.startswith("models/")
    ]
    assert foundation_violations == []


@pytest.mark.architecture
def test_historical_remains_lowest_pipeline_layer() -> None:
    historical_layer = PIPELINE_PACKAGES["historical"]
    for package, layer in PIPELINE_PACKAGES.items():
        if package == "historical":
            continue
        assert layer > historical_layer


@pytest.mark.architecture
def test_connectors_import_historical_layer() -> None:
    connectors_layer = PIPELINE_PACKAGES["connectors"]
    historical_layer = PIPELINE_PACKAGES["historical"]
    assert connectors_layer > historical_layer


@pytest.mark.architecture
def test_project_root_exists() -> None:
    assert (PROJECT_ROOT / "architecture" / "dependency_rules.py").is_file()

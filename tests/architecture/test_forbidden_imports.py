"""Architecture tests for forbidden import pairs."""

from __future__ import annotations

import pytest

from architecture.dependency_rules import FORBIDDEN_IMPORT_PAIRS


@pytest.mark.architecture
def test_forbidden_import_rules_are_defined() -> None:
    assert "services" in FORBIDDEN_IMPORT_PAIRS
    assert "connectors" in FORBIDDEN_IMPORT_PAIRS["services"]
    assert "ai" in FORBIDDEN_IMPORT_PAIRS["ml"]
    assert "decision" in FORBIDDEN_IMPORT_PAIRS["ai"]
    assert "connectors" in FORBIDDEN_IMPORT_PAIRS["ml"]
    assert "connectors" in FORBIDDEN_IMPORT_PAIRS["decision"]
    assert "connectors" in FORBIDDEN_IMPORT_PAIRS["risk"]
    assert "research" in FORBIDDEN_IMPORT_PAIRS["api"]


@pytest.mark.architecture
def test_no_forbidden_import_violations(architecture_report) -> None:
    violations = [
        violation
        for violation in architecture_report.violations
        if violation.rule_name == "forbidden_import"
    ]
    assert violations == []


@pytest.mark.architecture
def test_core_must_not_import_forbidden_layers() -> None:
    blocked = FORBIDDEN_IMPORT_PAIRS["core"]
    assert blocked == frozenset(
        {
            "feature_store",
            "training_pipeline",
            "model_registry",
            "inference_pipeline",
            "ml_runtime",
            "ml_engine_plugins",
            "framework_adapters",
            "artifact_management",
            "storage_providers",
            "ai",
            "connectors",
            "ml",
            "llm",
            "decision",
            "risk",
            "execution",
            "api",
            "dashboard",
            "research",
        }
    )


@pytest.mark.architecture
def test_ml_must_not_import_forbidden_layers() -> None:
    blocked = FORBIDDEN_IMPORT_PAIRS["ml"]
    assert blocked == frozenset(
        {
            "ai",
            "llm",
            "decision",
            "risk",
            "execution",
            "connectors",
            "api",
            "dashboard",
            "research",
        }
    )


@pytest.mark.architecture
def test_data_must_not_import_forbidden_layers() -> None:
    blocked = FORBIDDEN_IMPORT_PAIRS["data"]
    assert "feature_store" in blocked


@pytest.mark.architecture
def test_feature_store_must_not_import_forbidden_layers() -> None:
    blocked = FORBIDDEN_IMPORT_PAIRS["feature_store"]
    assert blocked == frozenset(
        {
            "training_pipeline",
            "model_registry",
            "inference_pipeline",
            "ml_runtime",
            "ml_engine_plugins",
            "framework_adapters",
            "artifact_management",
            "storage_providers",
            "ml",
            "ai",
            "decision",
            "risk",
            "execution",
            "connectors",
            "api",
            "dashboard",
            "research",
            "services",
            "pipeline",
            "workflow",
        }
    )


@pytest.mark.architecture
def test_model_registry_must_not_import_forbidden_layers() -> None:
    blocked = FORBIDDEN_IMPORT_PAIRS["model_registry"]
    assert blocked == frozenset(
        {
            "inference_pipeline",
            "ml_runtime",
            "ml_engine_plugins",
            "framework_adapters",
            "artifact_management",
            "storage_providers",
            "ml",
            "ai",
            "llm",
            "decision",
            "risk",
            "execution",
            "connectors",
            "api",
            "dashboard",
            "research",
            "services",
            "pipeline",
            "workflow",
        }
    )


@pytest.mark.architecture
def test_training_pipeline_must_not_import_forbidden_layers() -> None:
    blocked = FORBIDDEN_IMPORT_PAIRS["training_pipeline"]
    assert blocked == frozenset(
        {
            "model_registry",
            "inference_pipeline",
            "ml_runtime",
            "ml_engine_plugins",
            "framework_adapters",
            "artifact_management",
            "storage_providers",
            "ml",
            "ai",
            "llm",
            "decision",
            "risk",
            "execution",
            "connectors",
            "api",
            "dashboard",
            "research",
            "services",
            "pipeline",
            "workflow",
        }
    )


@pytest.mark.architecture
def test_ai_must_not_import_forbidden_layers() -> None:
    blocked = FORBIDDEN_IMPORT_PAIRS["ai"]
    assert blocked == frozenset(
        {
            "decision",
            "risk",
            "execution",
            "connectors",
            "api",
            "dashboard",
            "research",
        }
    )


@pytest.mark.architecture
def test_decision_must_not_import_forbidden_layers() -> None:
    blocked = FORBIDDEN_IMPORT_PAIRS["decision"]
    assert blocked == frozenset(
        {
            "risk",
            "execution",
            "connectors",
            "api",
            "dashboard",
            "research",
        }
    )


@pytest.mark.architecture
def test_risk_must_not_import_forbidden_layers() -> None:
    blocked = FORBIDDEN_IMPORT_PAIRS["risk"]
    assert blocked == frozenset(
        {
            "execution",
            "connectors",
            "api",
            "dashboard",
            "research",
        }
    )


@pytest.mark.architecture
def test_ml_engine_plugins_must_not_import_forbidden_layers() -> None:
    blocked = FORBIDDEN_IMPORT_PAIRS["ml_engine_plugins"]
    assert blocked == frozenset(
        {
            "framework_adapters",
            "artifact_management",
            "storage_providers",
            "ml",
            "ai",
            "llm",
            "decision",
            "risk",
            "execution",
            "connectors",
            "api",
            "dashboard",
            "research",
            "services",
            "pipeline",
            "workflow",
        }
    )


@pytest.mark.architecture
def test_ml_runtime_must_not_import_forbidden_layers() -> None:
    blocked = FORBIDDEN_IMPORT_PAIRS["ml_runtime"]
    assert blocked == frozenset(
        {
            "ml_engine_plugins",
            "framework_adapters",
            "artifact_management",
            "storage_providers",
            "ml",
            "ai",
            "llm",
            "decision",
            "risk",
            "execution",
            "connectors",
            "api",
            "dashboard",
            "research",
            "services",
            "pipeline",
            "workflow",
        }
    )


@pytest.mark.architecture
def test_inference_pipeline_must_not_import_forbidden_layers() -> None:
    blocked = FORBIDDEN_IMPORT_PAIRS["inference_pipeline"]
    assert blocked == frozenset(
        {
            "ml_runtime",
            "ml_engine_plugins",
            "framework_adapters",
            "artifact_management",
            "storage_providers",
            "ml",
            "ai",
            "llm",
            "decision",
            "risk",
            "execution",
            "connectors",
            "api",
            "dashboard",
            "research",
            "services",
            "pipeline",
            "workflow",
        }
    )


@pytest.mark.architecture
def test_framework_adapters_must_not_import_forbidden_layers() -> None:
    blocked = FORBIDDEN_IMPORT_PAIRS["framework_adapters"]
    assert blocked == frozenset(
        {
            "artifact_management",
            "storage_providers",
            "ml",
            "ai",
            "llm",
            "decision",
            "risk",
            "execution",
            "connectors",
            "api",
            "dashboard",
            "research",
            "services",
            "pipeline",
            "workflow",
        }
    )


@pytest.mark.architecture
def test_artifact_management_must_not_import_forbidden_layers() -> None:
    blocked = FORBIDDEN_IMPORT_PAIRS["artifact_management"]
    assert blocked == frozenset(
        {
            "storage_providers",
            "ml",
            "ai",
            "llm",
            "decision",
            "risk",
            "execution",
            "connectors",
            "api",
            "dashboard",
            "research",
            "services",
            "pipeline",
            "workflow",
        }
    )


@pytest.mark.architecture
def test_storage_providers_must_not_import_forbidden_layers() -> None:
    blocked = FORBIDDEN_IMPORT_PAIRS["storage_providers"]
    assert blocked == frozenset(
        {
            "ml",
            "ai",
            "llm",
            "decision",
            "risk",
            "execution",
            "connectors",
            "api",
            "dashboard",
            "research",
            "services",
            "pipeline",
            "workflow",
        }
    )


@pytest.mark.architecture
def test_services_must_not_import_connectors_directly() -> None:
    blocked = FORBIDDEN_IMPORT_PAIRS["services"]
    assert blocked == frozenset({"connectors"})

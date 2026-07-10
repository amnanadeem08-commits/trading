"""Contract tests for model registry."""

from __future__ import annotations

import inspect

import pytest

from model_registry import (
    ApprovalPolicy,
    ApprovalRequest,
    ApprovalResult,
    ExperimentRun,
    ExperimentSnapshot,
    LineageGraph,
    ModelCatalog,
    ModelRegistry,
    ModelRegistryRuntime,
    PromotionRegistry,
    RegisteredModel,
    RegistryLifecycleManager,
    RegistryValidator,
    RegistryVersionRegistry,
    build_model_registry_runtime,
    register_model_from_training,
)


@pytest.mark.contract
def test_registered_model_contract() -> None:
    fields = set(RegisteredModel.model_fields)
    assert "metadata" in fields
    assert "status" in fields


@pytest.mark.contract
def test_model_registry_contract() -> None:
    methods = {name for name, _ in inspect.getmembers(ModelRegistry, predicate=inspect.isfunction)}
    assert "register_model" in methods
    assert "register_version" in methods
    assert "promote" in methods
    assert "archive" in methods
    assert "lookup" in methods
    assert "latest" in methods
    assert "versions" in methods


@pytest.mark.contract
def test_model_catalog_contract() -> None:
    methods = {name for name, _ in inspect.getmembers(ModelCatalog, predicate=inspect.isfunction)}
    assert "list_models" in methods
    assert "list_versions" in methods
    assert "list_metadata" in methods


@pytest.mark.contract
def test_promotion_registry_contract() -> None:
    methods = {
        name for name, _ in inspect.getmembers(PromotionRegistry, predicate=inspect.isfunction)
    }
    assert "record_transition" in methods
    assert "create_approval_request" in methods
    assert "resolve_approval" in methods


@pytest.mark.contract
def test_lineage_graph_contract() -> None:
    methods = {name for name, _ in inspect.getmembers(LineageGraph, predicate=inspect.isfunction)}
    assert "add_node" in methods
    assert "add_edge" in methods
    assert "record_training_lineage" in methods


@pytest.mark.contract
def test_registry_validator_contract() -> None:
    methods = {
        name for name, _ in inspect.getmembers(RegistryValidator, predicate=inspect.isfunction)
    }
    assert "validate_model" in methods
    assert "validate_version" in methods
    assert "validate_promotion" in methods


@pytest.mark.contract
def test_registry_lifecycle_contract() -> None:
    methods = {
        name
        for name, _ in inspect.getmembers(RegistryLifecycleManager, predicate=inspect.isfunction)
    }
    assert "emit_model_registered" in methods
    assert "emit_version_registered" in methods
    assert "emit_promotion_requested" in methods
    assert "emit_promotion_approved" in methods


@pytest.mark.contract
def test_experiment_run_contract() -> None:
    fields = set(ExperimentRun.model_fields)
    assert "run_id" in fields
    assert "artifact_id" in fields
    assert "parameters" in fields


@pytest.mark.contract
def test_experiment_snapshot_contract() -> None:
    fields = set(ExperimentSnapshot.model_fields)
    assert "snapshot_id" in fields
    assert "immutable" in fields


@pytest.mark.contract
def test_approval_contracts() -> None:
    assert "policy_id" in ApprovalPolicy.model_fields
    assert "request_id" in ApprovalRequest.model_fields
    assert "state" in ApprovalResult.model_fields


@pytest.mark.contract
def test_registry_version_registry_contract() -> None:
    methods = {
        name
        for name, _ in inspect.getmembers(RegistryVersionRegistry, predicate=inspect.isfunction)
    }
    assert "register" in methods
    assert "latest" in methods


@pytest.mark.contract
def test_integration_bridge_exports() -> None:
    methods = {
        name for name, _ in inspect.getmembers(ModelRegistryRuntime, predicate=inspect.isfunction)
    }
    assert "register_model" in methods
    assert "ingest_training_result" in methods
    assert "promote_version" in methods
    assert callable(build_model_registry_runtime)
    assert callable(register_model_from_training)

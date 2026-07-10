"""Contract tests for core layer."""

from __future__ import annotations

import inspect

import pytest

from core import (
    AuditContext,
    BaseEntity,
    CoreContext,
    ExecutionContext,
    IdentityContext,
    OperationContext,
    OperationResult,
    RequestContext,
    ResultStatus,
    SecurityContext,
)
from tests.core_helpers import SampleEntity, make_entity


@pytest.mark.contract
def test_base_entity_contract_methods() -> None:
    methods = {name for name, _ in inspect.getmembers(BaseEntity, predicate=inspect.isfunction)}
    assert "entity_id" in methods
    assert "name" in methods
    assert "version" in methods
    assert "entity_type" in methods
    assert "to_definition" in methods


@pytest.mark.contract
def test_sample_entity_satisfies_contract() -> None:
    entity = SampleEntity()
    definition = entity.to_definition()
    assert definition.entity_id == "sample-entity"
    assert definition.entity_type == "resource"


@pytest.mark.contract
def test_entity_model_fields() -> None:
    entity = make_entity()
    assert entity.entity_id == "sample-entity"
    assert entity.version == "1.0.0"
    assert entity.metadata["scope"] == "test"


@pytest.mark.contract
def test_operation_result_fields() -> None:
    result = OperationResult(operation_id="op-1", status=ResultStatus.SUCCESS)
    assert result.status.value == "success"
    assert result.errors == ()


@pytest.mark.contract
def test_core_context_contract_fields() -> None:
    context = CoreContext(
        trace_id="trace-1",
        correlation_id="corr-1",
        request=RequestContext(request_id="req-1"),
        execution=ExecutionContext(execution_id="exec-1"),
        operation=OperationContext(operation_id="op-1", operation_type="test"),
        identity=IdentityContext(),
        security=SecurityContext(),
        audit=AuditContext(
            audit_id="audit-1",
            action="test",
            resource_type="entity",
            resource_id="sample-entity",
        ),
    )
    assert context.trace_id == "trace-1"
    assert context.dataset_ids == ()

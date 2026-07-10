"""Unit tests for adapter runtime with ORT execution."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from framework_adapters import (
    ORT_ADAPTER_ID,
    AdapterRuntimeContext,
    AdapterRuntimeValidator,
    bootstrap_adapter_runtime,
    create_ort_adapter,
)
from tests.framework_adapters.ort_helpers import make_ort_artifact_bundle, ort_engine_type
from tests.storage_providers_helpers import make_local_storage_bridge

if TYPE_CHECKING:
    from pathlib import Path


@pytest.mark.unit
def test_storage_load_registers_ort_executor(tmp_path: Path) -> None:
    reference, metadata, manifest, _ = make_ort_artifact_bundle(tmp_path)
    ml_runtime, bridge, adapter_runtime = bootstrap_adapter_runtime()
    storage_bridge = make_local_storage_bridge(tmp_path)
    adapter = create_ort_adapter()

    executor = storage_bridge.load_through_adapter(
        adapter,
        reference=reference,
        metadata=metadata,
        manifest=manifest,
    )
    record = bridge.registry.lookup(ORT_ADAPTER_ID)
    bridge.register_executor(
        executor,
        name=record.metadata.name,
        version=record.metadata.version,
        capabilities=tuple(cap.value for cap in adapter.capabilities()),
    )

    assert executor.executor_id() == ORT_ADAPTER_ID
    ready = AdapterRuntimeValidator(registry=bridge.registry).validate_executor_ready(executor)
    assert ready.valid is True
    assert ml_runtime.registry.lookup(ORT_ADAPTER_ID) is executor
    assert adapter_runtime.initialized is True


@pytest.mark.unit
def test_adapter_runtime_selects_ort_adapter_by_format(tmp_path: Path) -> None:
    _reference, _metadata, _manifest, _ = make_ort_artifact_bundle(tmp_path)
    _ml_runtime, bridge, adapter_runtime = bootstrap_adapter_runtime()
    context = AdapterRuntimeContext(
        engine_type=ort_engine_type(),
        artifact_format="ort",
        artifact_reference="local://artifacts/ort-model/1.0.0/model.onnx",
        model_id="ort-model",
        executor_id=ORT_ADAPTER_ID,
    )
    selected = adapter_runtime.select_adapter(context)
    assert selected == ORT_ADAPTER_ID
    stats = bridge.metrics_collector.statistics()
    assert stats.adapter_usage >= 1

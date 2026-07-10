"""Contract tests for data layer."""

from __future__ import annotations

import pytest

from data import BaseDataset, DatasetResult, DatasetState, DatasetStatus
from tests.data_helpers import DerivedDataset, RecordsDataset, make_dataset


@pytest.mark.contract
def test_base_dataset_contract_methods() -> None:
    required = {
        "dataset_id",
        "name",
        "version",
        "schema",
        "load",
    }
    assert required.issubset(set(dir(BaseDataset)))
    for method_name in required:
        assert getattr(BaseDataset, method_name) is not None


@pytest.mark.contract
@pytest.mark.parametrize("dataset_type", [RecordsDataset, DerivedDataset])
def test_dataset_implementations_satisfy_contract(dataset_type: type[BaseDataset]) -> None:
    implementation = dataset_type()
    assert isinstance(implementation.dataset_id(), str)
    assert isinstance(implementation.name(), str)
    assert isinstance(implementation.version(), str)
    assert isinstance(implementation.schema().schema_id, str)
    assert isinstance(implementation.dependencies(), tuple)
    records = implementation.load()
    assert isinstance(records, tuple)


@pytest.mark.contract
def test_dataset_model_contract_fields() -> None:
    dataset = make_dataset()
    assert dataset.dataset_id == "sample-dataset"
    assert dataset.state == DatasetState.REGISTERED
    assert dataset.dependencies == ()


@pytest.mark.contract
def test_dataset_result_contract_fields() -> None:
    result = DatasetResult(
        dataset_id="records",
        status=DatasetStatus.COMPLETED,
        record_count=2,
        errors=(),
        warnings=(),
        metrics={},
    )
    assert result.status == DatasetStatus.COMPLETED
    assert result.record_count == 2

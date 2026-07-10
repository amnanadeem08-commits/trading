"""Additional data layer coverage tests."""

from __future__ import annotations

import pytest

from data import (
    TERMINAL_DATASET_STATES,
    CircularDatasetDependencyError,
    DataError,
    DatasetNotFoundError,
    DatasetPersistenceError,
    DatasetRegistrationError,
    DatasetState,
    DatasetStateError,
    DatasetVersion,
    DatasetVersionRegistry,
    InMemoryDatasetCache,
    InMemoryDatasetPersistenceStore,
    SchemaValidationError,
    SchemaValidator,
    build_dependency_graph,
    dataset_metadata,
    deserialize_metadata,
    detect_cycle,
    serialize_metadata,
    topological_order,
)
from data.dependency import DependencyGraph
from tests.data_helpers import RecordsDataset, make_dataset, make_schema


def test_data_exceptions_expose_codes() -> None:
    assert DataError("x").code == "data_error"
    assert DatasetNotFoundError("x").code == "dataset_not_found"
    assert DatasetRegistrationError("x").code == "dataset_registration_error"
    cycle = CircularDatasetDependencyError(("a", "b", "a"))
    assert cycle.cycle == ("a", "b", "a")
    assert SchemaValidationError("x", field_name="id").field_name == "id"
    assert DatasetStateError("id", "draft", "load").operation == "load"


@pytest.mark.unit
def test_terminal_dataset_states() -> None:
    assert DatasetState.READY in TERMINAL_DATASET_STATES
    assert DatasetState.DRAFT not in TERMINAL_DATASET_STATES


@pytest.mark.unit
def test_dataset_metadata_decorator() -> None:
    metadata = dataset_metadata(RecordsDataset)
    assert metadata["dataset_id"] == "records"
    assert metadata["auto_register"] is False


@pytest.mark.unit
def test_serialize_deserialize_metadata() -> None:
    dataset = make_dataset()
    payload = serialize_metadata(dataset.metadata)
    restored = deserialize_metadata(payload)
    assert restored.dataset_id == dataset.metadata.dataset_id


@pytest.mark.unit
def test_deserialize_metadata_from_dict() -> None:
    dataset = make_dataset()
    restored = deserialize_metadata(dataset.metadata.model_dump())
    assert restored.name == dataset.metadata.name


@pytest.mark.unit
def test_in_memory_persistence_store() -> None:
    store = InMemoryDatasetPersistenceStore()
    dataset = make_dataset(dataset_id="persisted")
    store.save(dataset)
    assert store.load("persisted").dataset_id == "persisted"
    assert store.list() == ("persisted",)
    store.delete("persisted")
    assert store.list() == ()


@pytest.mark.unit
def test_in_memory_persistence_store_empty_id_raises() -> None:
    store = InMemoryDatasetPersistenceStore()
    dataset = make_dataset(dataset_id=" ")
    with pytest.raises(DatasetPersistenceError):
        store.save(dataset)


@pytest.mark.unit
def test_in_memory_persistence_store_missing_raises() -> None:
    store = InMemoryDatasetPersistenceStore()
    with pytest.raises(DatasetNotFoundError):
        store.load("missing")


@pytest.mark.unit
def test_in_memory_cache_operations() -> None:
    cache = InMemoryDatasetCache(max_entries=2)
    records = ({"id": "1", "value": 1},)
    cache.set("a", records)
    assert cache.get("a") == records
    cache.invalidate("a")
    assert cache.get("a") is None
    cache.set("b", records)
    cache.clear()
    assert cache.size() == 0


@pytest.mark.unit
def test_in_memory_cache_evicts_oldest() -> None:
    cache = InMemoryDatasetCache(max_entries=1)
    records = ({"id": "1", "value": 1},)
    cache.set("first", records)
    cache.set("second", records)
    assert cache.get("first") is None
    assert cache.get("second") == records


@pytest.mark.unit
def test_dependency_graph_utilities() -> None:
    graph = build_dependency_graph(
        ("a", "b"),
        {"a": ("b",), "b": ()},
    )
    assert detect_cycle(graph) is None
    order = topological_order(graph)
    assert order == ("b", "a")


@pytest.mark.unit
def test_dependency_graph_cycle_detection() -> None:
    graph = DependencyGraph(
        nodes=("a", "b"),
        edges={"a": ("b",), "b": ("a",)},
    )
    cycle = detect_cycle(graph)
    assert cycle is not None


@pytest.mark.unit
def test_dependency_graph_topological_failure() -> None:
    graph = DependencyGraph(
        nodes=("a", "b"),
        edges={"a": ("b",), "b": ("a",)},
    )
    with pytest.raises(ValueError):
        topological_order(graph)


@pytest.mark.unit
def test_schema_validator_assert_valid_raises() -> None:
    validator = SchemaValidator(make_schema())
    with pytest.raises(SchemaValidationError):
        validator.assert_valid({"id": "1"})


@pytest.mark.unit
def test_schema_validator_validate_records() -> None:
    validator = SchemaValidator(make_schema())
    result = validator.validate_records(({"id": "1", "value": 1}, {"id": "2"}))
    assert result.valid is False
    assert any("Record 1" in error for error in result.errors)


@pytest.mark.unit
def test_schema_nullable_and_object_types() -> None:
    schema = make_schema().model_copy(
        update={
            "fields": (
                make_schema().fields[0].model_copy(update={"nullable": True}),
                make_schema().fields[1].model_copy(update={"field_type": "object"}),
            )
        }
    )
    errors = schema.validate_record({"id": None, "value": {"nested": True}})
    assert errors == ()


@pytest.mark.unit
def test_dataset_version_registry() -> None:
    registry = DatasetVersionRegistry()
    registry.register(DatasetVersion(dataset_id="records", version="1.0.0"))
    registry.register(DatasetVersion(dataset_id="records", version="1.0.1"))
    versions = registry.list_versions("records")
    assert len(versions) == 2
    assert registry.latest("records").version == "1.0.1"
    assert registry.list_datasets() == ("records",)


@pytest.mark.unit
def test_dataset_version_registry_missing_raises() -> None:
    registry = DatasetVersionRegistry()
    with pytest.raises(DatasetNotFoundError):
        registry.list_versions("missing")


@pytest.mark.unit
def test_base_dataset_to_definition() -> None:
    implementation = RecordsDataset()
    definition = implementation.to_definition(state=DatasetState.READY)
    assert definition.dataset_id == "records"
    assert definition.state == DatasetState.READY


@pytest.mark.unit
def test_base_dataset_transform_default() -> None:
    implementation = RecordsDataset()
    records = implementation.load()
    assert implementation.transform(records) == records

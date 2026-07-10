"""Dataset validation."""

from __future__ import annotations

from dataclasses import dataclass

from data.dataset import Dataset
from data.dependency import build_dependency_graph, detect_cycle, topological_order
from data.exceptions import CircularDatasetDependencyError
from data.schema import DatasetSchema


@dataclass(frozen=True)
class DatasetValidationResult:
    """Outcome of dataset validation."""

    valid: bool
    errors: tuple[str, ...] = ()
    execution_order: tuple[str, ...] = ()


def _datasets_by_id(datasets: tuple[Dataset, ...]) -> dict[str, Dataset]:
    return {item.dataset_id: item for item in datasets}


def validate_dataset(dataset: Dataset) -> DatasetValidationResult:
    """Validate a single dataset definition and schema."""
    errors: list[str] = []
    if not dataset.dataset_id.strip():
        errors.append("Dataset id must not be empty")
    if not dataset.name.strip():
        errors.append("Dataset name must not be empty")
    if not dataset.version.strip():
        errors.append("Dataset version must not be empty")
    if dataset.metadata.dataset_id != dataset.dataset_id:
        errors.append(
            f"Metadata dataset_id mismatch: {dataset.metadata.dataset_id} != {dataset.dataset_id}"
        )
    schema_errors = _validate_schema(dataset.dataset_schema)
    errors.extend(schema_errors)
    for dependency in dataset.dependencies:
        if dependency == dataset.dataset_id:
            errors.append(f"Dataset depends on itself: {dataset.dataset_id}")

    if errors:
        return DatasetValidationResult(valid=False, errors=tuple(errors))
    return DatasetValidationResult(valid=True)


def validate_dataset_set(datasets: tuple[Dataset, ...]) -> DatasetValidationResult:
    """Validate a set of datasets including dependency ordering."""
    errors: list[str] = []
    by_id = _datasets_by_id(datasets)
    dataset_ids = [item.dataset_id for item in datasets]
    if len(dataset_ids) != len(set(dataset_ids)):
        errors.append("Duplicate dataset identifiers detected")

    for item in datasets:
        result = validate_dataset(item)
        if not result.valid:
            errors.extend(result.errors)
        for dependency in item.dependencies:
            if dependency not in by_id:
                errors.append(f"Missing dependency '{dependency}' required by '{item.dataset_id}'")

    if errors:
        return DatasetValidationResult(valid=False, errors=tuple(errors))

    dependencies = {item.dataset_id: item.dependencies for item in datasets}
    graph = build_dependency_graph(tuple(by_id.keys()), dependencies)
    cycle = detect_cycle(graph)
    if cycle is not None:
        raise CircularDatasetDependencyError(cycle)

    return DatasetValidationResult(
        valid=True,
        execution_order=topological_order(graph),
    )


def _validate_schema(schema: DatasetSchema) -> tuple[str, ...]:
    errors: list[str] = []
    if not schema.schema_id.strip():
        errors.append("Schema id must not be empty")
    field_names = [field.name for field in schema.fields]
    if len(field_names) != len(set(field_names)):
        errors.append(f"Duplicate schema fields detected in '{schema.schema_id}'")
    return tuple(errors)

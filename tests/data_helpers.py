"""Helpers for data layer tests."""

from __future__ import annotations

from data.dataset import BaseDataset, Dataset
from data.decorators import dataset
from data.metadata import DatasetMetadata
from data.schema import DatasetSchema, SchemaField
from data.state import DatasetState


def make_schema(*, schema_id: str = "test-schema", version: str = "1.0.0") -> DatasetSchema:
    return DatasetSchema(
        schema_id=schema_id,
        version=version,
        fields=(
            SchemaField(name="id", field_type="string", required=True),
            SchemaField(name="value", field_type="integer", required=True),
        ),
    )


def make_dataset(
    *,
    dataset_id: str = "sample-dataset",
    name: str = "Sample Dataset",
    version: str = "1.0.0",
    dependencies: tuple[str, ...] = (),
    state: DatasetState = DatasetState.REGISTERED,
) -> Dataset:
    schema = make_schema()
    metadata = DatasetMetadata(dataset_id=dataset_id, name=name, version=version)
    return Dataset(
        dataset_id=dataset_id,
        name=name,
        version=version,
        dataset_schema=schema,
        metadata=metadata,
        state=state,
        dependencies=dependencies,
    )


@dataset(dataset_id="records", auto_register=False)
class RecordsDataset(BaseDataset):
    """Primary test dataset with sample records."""

    def dataset_id(self) -> str:
        return "records"

    def name(self) -> str:
        return "Records Dataset"

    def version(self) -> str:
        return "1.0.0"

    def schema(self) -> DatasetSchema:
        return make_schema(schema_id="records-schema")

    def load(self) -> tuple[dict[str, object], ...]:
        return ({"id": "1", "value": 10}, {"id": "2", "value": 20})


@dataset(dataset_id="derived", auto_register=False)
class DerivedDataset(BaseDataset):
    """Dependent test dataset."""

    def dataset_id(self) -> str:
        return "derived"

    def name(self) -> str:
        return "Derived Dataset"

    def version(self) -> str:
        return "1.0.0"

    def schema(self) -> DatasetSchema:
        return make_schema(schema_id="derived-schema")

    def dependencies(self) -> tuple[str, ...]:
        return ("records",)

    def load(self) -> tuple[dict[str, object], ...]:
        return ({"id": "3", "value": 30},)

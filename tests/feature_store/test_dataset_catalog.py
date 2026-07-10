"""Unit tests for dataset catalog."""

from __future__ import annotations

import pytest

from feature_store import DatasetCatalog, DatasetCatalogEntry
from feature_store.exceptions import DatasetNotFoundError


@pytest.mark.unit
def test_catalog_register_and_lookup() -> None:
    catalog = DatasetCatalog()
    entry = DatasetCatalogEntry(
        dataset_id="dataset-1",
        name="Sample",
        version="1.0.0",
        schema_id="feature-schema-v1",
        symbol_id="symbol-1",
        capabilities=("offline", "online"),
        lineage=("dataset-1",),
    )
    catalog.register(entry)
    resolved = catalog.lookup("dataset-1")
    assert resolved.name == "Sample"
    assert catalog.capabilities("dataset-1") == ("offline", "online")


@pytest.mark.unit
def test_catalog_list() -> None:
    catalog = DatasetCatalog()
    catalog.register(
        DatasetCatalogEntry(
            dataset_id="alpha",
            name="Alpha",
            version="1.0.0",
            schema_id="schema",
            symbol_id="symbol-1",
        )
    )
    catalog.register(
        DatasetCatalogEntry(
            dataset_id="beta",
            name="Beta",
            version="1.0.0",
            schema_id="schema",
            symbol_id="symbol-1",
        )
    )
    assert catalog.list() == ("alpha", "beta")


@pytest.mark.unit
def test_catalog_missing_raises() -> None:
    catalog = DatasetCatalog()
    with pytest.raises(DatasetNotFoundError):
        catalog.lookup("missing")

"""Unit tests for feature store validation."""

from __future__ import annotations

import pytest

from feature_store import FeatureStoreValidator, compute_feature_dataset_hash
from tests.feature_store_helpers import make_feature_dataset, make_feature_record


@pytest.mark.unit
def test_validate_record_success() -> None:
    validator = FeatureStoreValidator()
    result = validator.validate_record(make_feature_record())
    assert result.valid is True


@pytest.mark.unit
def test_validate_record_missing() -> None:
    validator = FeatureStoreValidator()
    result = validator.validate_record(None)
    assert result.valid is False


@pytest.mark.unit
def test_validate_records_duplicates() -> None:
    validator = FeatureStoreValidator()
    record = make_feature_record(record_id="duplicate")
    result = validator.validate_records((record, record))
    assert result.valid is False


@pytest.mark.unit
def test_validate_dataset() -> None:
    validator = FeatureStoreValidator()
    dataset = make_feature_dataset()
    records = (make_feature_record(record_id="r1"), make_feature_record(record_id="r2"))
    dataset = dataset.with_record_count(2)
    result = validator.validate_dataset(dataset, records=records)
    assert result.checks["record_count_match"] is True


@pytest.mark.unit
def test_validate_checksum() -> None:
    validator = FeatureStoreValidator()
    records = (make_feature_record(),)
    checksum = compute_feature_dataset_hash(tuple(item.values for item in records))
    dataset = make_feature_dataset().with_record_count(1).with_checksum(checksum)
    result = validator.validate_checksum(dataset, records=records)
    assert result.valid is True


@pytest.mark.unit
def test_validate_record_empty_values() -> None:
    validator = FeatureStoreValidator()
    record = make_feature_record().model_copy(update={"values": {}})
    result = validator.validate_record(record)
    assert result.valid is False


@pytest.mark.unit
def test_validate_checksum_mismatch() -> None:
    validator = FeatureStoreValidator()
    dataset = make_feature_dataset().with_checksum("invalid")
    records = (make_feature_record(),)
    result = validator.validate_checksum(dataset, records=records)
    assert result.valid is False


@pytest.mark.unit
def test_exception_types() -> None:
    from feature_store.exceptions import FeatureStoreValidationError, SnapshotNotFoundError

    assert SnapshotNotFoundError("snap-1").snapshot_id == "snap-1"
    assert FeatureStoreValidationError("invalid").code == "feature_store_validation_error"

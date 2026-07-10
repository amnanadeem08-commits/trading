"""Unit tests for historical validation."""

from __future__ import annotations

from historical import HistoricalValidator, Repository
from tests.historical_helpers import make_sample_dataset, make_sample_record, seed_repository


def test_validate_dataset_success() -> None:
    validator = HistoricalValidator()
    result = validator.validate_dataset(make_sample_dataset())
    assert result.valid is True


def test_validate_dataset_missing() -> None:
    validator = HistoricalValidator()
    result = validator.validate_dataset(None)
    assert result.valid is False


def test_validate_schema() -> None:
    validator = HistoricalValidator()
    dataset = make_sample_dataset()
    record = make_sample_record()
    result = validator.validate_schema(dataset, record)
    assert result.valid is True


def test_validate_timestamps() -> None:
    repository = Repository()
    seed_repository(repository)
    records = repository.load("dataset-1")
    validator = HistoricalValidator()
    result = validator.validate_timestamps(records)
    assert result.valid is True


def test_validate_duplicates() -> None:
    validator = HistoricalValidator()
    record = make_sample_record()
    result = validator.validate_duplicates((record, record))
    assert result.valid is False


def test_validate_metadata() -> None:
    validator = HistoricalValidator()
    result = validator.validate_metadata(make_sample_dataset())
    assert result.valid is True


def test_validate_all() -> None:
    repository = Repository()
    dataset = seed_repository(repository)
    records = repository.load("dataset-1")
    validator = HistoricalValidator()
    result = validator.validate_all(dataset, records)
    assert result.valid is True

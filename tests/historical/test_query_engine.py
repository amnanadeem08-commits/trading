"""Unit tests for query engine."""

from __future__ import annotations

from datetime import UTC, datetime

from historical import QueryEngine, QueryFilters, QueryRequest, QueryType, Repository
from tests.historical_helpers import make_sample_dataset, seed_repository


def test_query_lookup_by_id() -> None:
    repository = Repository()
    seed_repository(repository)
    engine = QueryEngine(repository)
    result = engine.lookup_by_id("dataset-1")
    assert result.matched is True
    assert result.total == 3
    assert len(result.records) == 3


def test_query_lookup_by_version() -> None:
    repository = Repository()
    seed_repository(repository)
    engine = QueryEngine(repository)
    result = engine.lookup_by_version("dataset-1", version="1.0.0")
    assert result.matched is True
    assert result.datasets[0].version == "1.0.0"


def test_query_time_range() -> None:
    repository = Repository()
    seed_repository(repository)
    engine = QueryEngine(repository)
    result = engine.query_time_range(
        "dataset-1",
        start_timestamp=datetime(2026, 1, 1, 12, 1, 0, tzinfo=UTC),
        end_timestamp=datetime(2026, 1, 1, 12, 2, 0, tzinfo=UTC),
    )
    assert result.matched is True
    assert result.total == 2


def test_query_metadata() -> None:
    repository = Repository()
    repository.register_dataset(make_sample_dataset(tags=("alpha", "beta")))
    engine = QueryEngine(repository)
    result = engine.execute(QueryRequest(query_type=QueryType.METADATA))
    assert result.matched is True
    assert result.total == 1


def test_query_tags() -> None:
    repository = Repository()
    repository.register_dataset(make_sample_dataset(tags=("alpha", "beta")))
    engine = QueryEngine(repository)
    result = engine.execute(
        QueryRequest(
            query_type=QueryType.TAG,
            filters=QueryFilters(tags=("alpha",)),
        )
    )
    assert result.matched is True


def test_query_cursor() -> None:
    repository = Repository()
    seed_repository(repository)
    engine = QueryEngine(repository)
    result = engine.execute(
        QueryRequest(
            query_type=QueryType.CURSOR,
            filters=QueryFilters(
                dataset_id="dataset-1",
                version="1.0.0",
                cursor_position=1,
            ),
        )
    )
    assert result.matched is True
    assert result.records[0].sequence == 1

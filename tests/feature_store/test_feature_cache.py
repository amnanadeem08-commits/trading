"""Unit tests for feature cache."""

from __future__ import annotations

import pytest

from feature_store import FeatureCache
from feature_store.exceptions import DatasetNotFoundError
from tests.feature_store_helpers import make_feature_record


@pytest.mark.unit
def test_offline_cache_roundtrip() -> None:
    cache = FeatureCache()
    records = (make_feature_record(record_id="record-1"),)
    cache.cache_offline("dataset-1", records)
    resolved = cache.get_offline("dataset-1")
    assert len(resolved) == 1


@pytest.mark.unit
def test_online_cache_roundtrip() -> None:
    cache = FeatureCache()
    record = make_feature_record(record_id="online-1")
    cache.cache_online("key-1", record)
    resolved = cache.get_online("key-1")
    assert resolved.record_id == "online-1"


@pytest.mark.unit
def test_invalidate_and_clear() -> None:
    cache = FeatureCache()
    cache.cache_offline("dataset-1", (make_feature_record(),))
    cache.invalidate("dataset-1")
    with pytest.raises(DatasetNotFoundError):
        cache.get_offline("dataset-1")
    cache.cache_online("key-1", make_feature_record())
    cache.clear()
    with pytest.raises(DatasetNotFoundError):
        cache.get_online("key-1")


@pytest.mark.unit
def test_cache_capacity_eviction() -> None:
    cache = FeatureCache(max_entries=1)
    cache.cache_online("key-1", make_feature_record(record_id="first"))
    cache.cache_online("key-2", make_feature_record(record_id="second"))
    assert cache.get_online("key-2").record_id == "second"

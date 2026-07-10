"""Unit tests for artifact cache."""

from __future__ import annotations

import pytest

from artifact_management import ArtifactCache, ArtifactCacheError, ArtifactNotFoundError
from tests.artifact_management_helpers import STUB_ARTIFACT_ID, make_stub_artifact_reference


@pytest.mark.unit
def test_artifact_cache_put_and_get() -> None:
    cache = ArtifactCache()
    reference = make_stub_artifact_reference()
    cache.put(reference)
    entry = cache.get(STUB_ARTIFACT_ID)
    assert entry.artifact_id == STUB_ARTIFACT_ID
    assert entry.hit_count == 1
    assert cache.hits == 1


@pytest.mark.unit
def test_artifact_cache_miss() -> None:
    cache = ArtifactCache()
    with pytest.raises(ArtifactNotFoundError):
        cache.get("missing")
    assert cache.misses == 1


@pytest.mark.unit
def test_artifact_cache_remove_and_clear() -> None:
    cache = ArtifactCache()
    cache.put(make_stub_artifact_reference())
    cache.remove(STUB_ARTIFACT_ID)
    with pytest.raises(ArtifactNotFoundError):
        cache.get(STUB_ARTIFACT_ID)
    cache.put(make_stub_artifact_reference())
    cache.clear()
    assert cache.contains(STUB_ARTIFACT_ID) is False


@pytest.mark.unit
def test_artifact_cache_remove_missing_raises() -> None:
    cache = ArtifactCache()
    with pytest.raises(ArtifactCacheError):
        cache.remove("missing")

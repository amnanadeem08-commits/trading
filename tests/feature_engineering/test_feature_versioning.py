"""Unit tests for feature versioning."""

from __future__ import annotations

import pytest

from feature_engineering import FeatureVersion, FeatureVersionRegistry
from feature_engineering.exceptions import FeatureNotFoundError, FeatureVersionError


@pytest.mark.unit
def test_register_and_latest_version() -> None:
    registry = FeatureVersionRegistry()
    version = FeatureVersion(
        feature_id="feature-1",
        version="1.0.0",
        schema_id="feature-schema-v1",
        snapshot_id="snap-1",
    )
    registry.register(version)
    latest = registry.latest("feature-1")
    assert latest.version == "1.0.0"


@pytest.mark.unit
def test_list_versions_and_features() -> None:
    registry = FeatureVersionRegistry()
    registry.register(
        FeatureVersion(
            feature_id="feature-1",
            version="1.0.0",
            schema_id="feature-schema-v1",
            snapshot_id="snap-1",
        )
    )
    registry.register(
        FeatureVersion(
            feature_id="feature-1",
            version="1.1.0",
            schema_id="feature-schema-v1",
            snapshot_id="snap-2",
        )
    )
    versions = registry.list_versions("feature-1")
    assert len(versions) == 2
    assert registry.list_features() == ("feature-1",)


@pytest.mark.unit
def test_snapshot_lookup() -> None:
    registry = FeatureVersionRegistry()
    registry.register(
        FeatureVersion(
            feature_id="feature-1",
            version="1.0.0",
            schema_id="feature-schema-v1",
            snapshot_id="snap-lookup",
        )
    )
    resolved = registry.snapshot("snap-lookup")
    assert resolved.feature_id == "feature-1"


@pytest.mark.unit
def test_missing_feature_raises() -> None:
    registry = FeatureVersionRegistry()
    with pytest.raises(FeatureNotFoundError):
        registry.latest("missing")


@pytest.mark.unit
def test_missing_snapshot_raises() -> None:
    registry = FeatureVersionRegistry()
    with pytest.raises(FeatureVersionError):
        registry.snapshot("missing")

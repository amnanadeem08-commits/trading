"""Unit tests for artifact metrics."""

from __future__ import annotations

import pytest

from artifact_management import ArtifactMetricsCollector, ArtifactState, ArtifactSummary
from tests.artifact_management_helpers import STUB_ARTIFACT_ID, STUB_ARTIFACT_URI


@pytest.mark.unit
def test_artifact_metrics_collector_records_operations() -> None:
    collector = ArtifactMetricsCollector()
    collector.record_registration()
    collector.record_resolution()
    collector.record_validation()
    collector.record_cache_hit()
    collector.record_cache_miss()
    collector.record_failure()
    collector.record_state(ArtifactState.CACHED)
    collector.record_summary(
        ArtifactSummary(
            artifact_id=STUB_ARTIFACT_ID,
            name="Stub",
            version="1.0.0",
            state=ArtifactState.CACHED,
            uri=STUB_ARTIFACT_URI,
        )
    )
    stats = collector.statistics()
    assert stats.artifact_registrations == 1
    assert stats.artifact_resolutions == 1
    assert stats.artifact_validations == 1
    assert stats.cache_hits == 1
    assert stats.cache_misses == 1
    assert stats.artifact_failures == 1
    assert collector.get_summary(STUB_ARTIFACT_ID) is not None

"""Unit tests for provider metrics."""

from __future__ import annotations

import pytest

from storage_providers import ProviderMetricsCollector, ProviderState
from storage_providers.providers import STUB_LOCAL_PROVIDER_ID, create_stub_local_provider


@pytest.mark.unit
def test_provider_metrics_collector_records_operations() -> None:
    collector = ProviderMetricsCollector()
    collector.record_registration()
    collector.record_resolution()
    collector.record_validation()
    collector.record_state(ProviderState.REGISTERED)
    stats = collector.statistics()
    assert stats.provider_registrations == 1
    assert stats.provider_resolutions == 1
    assert stats.provider_validations == 1
    assert stats.registered_providers == 1


@pytest.mark.unit
def test_provider_metrics_collector_records_cache_and_failures() -> None:
    collector = ProviderMetricsCollector()
    collector.record_cache_hit()
    collector.record_cache_miss()
    collector.record_validation_failure()
    collector.record_resolution_failure()
    collector.record_provider_usage(STUB_LOCAL_PROVIDER_ID)
    stats = collector.statistics()
    assert stats.cache_hits == 1
    assert stats.cache_misses == 1
    assert stats.validation_failures == 1
    assert stats.resolution_failures == 1
    assert stats.provider_usage[STUB_LOCAL_PROVIDER_ID] == 1


@pytest.mark.unit
def test_provider_metrics_collector_records_summary() -> None:
    collector = ProviderMetricsCollector()
    provider = create_stub_local_provider()
    collector.record_summary_from_provider(
        provider, state=ProviderState.REGISTERED, uri_scheme="local"
    )
    summary = collector.get_summary(STUB_LOCAL_PROVIDER_ID)
    assert summary is not None
    assert summary.name == "Stub Local Provider"

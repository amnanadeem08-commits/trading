"""Unit tests for artifact health."""

from __future__ import annotations

import pytest

from artifact_management import ArtifactHealthChecker, ArtifactRegistry, ArtifactState, HealthStatus
from tests.artifact_management_helpers import STUB_ARTIFACT_ID, make_stub_artifact_bundle


@pytest.mark.unit
def test_artifact_health_checker_reports_healthy() -> None:
    registry = ArtifactRegistry()
    reference, metadata, manifest = make_stub_artifact_bundle()
    registry.register(metadata=metadata, manifest=manifest, reference=reference)
    checker = ArtifactHealthChecker(registry=registry)
    result = checker.check(STUB_ARTIFACT_ID)
    assert result.status == HealthStatus.HEALTHY


@pytest.mark.unit
def test_artifact_health_checker_unhealthy_failed_state() -> None:
    registry = ArtifactRegistry()
    reference, metadata, manifest = make_stub_artifact_bundle()
    registry.register(metadata=metadata, manifest=manifest, reference=reference)
    registry.update_state(STUB_ARTIFACT_ID, ArtifactState.FAILED)
    checker = ArtifactHealthChecker(registry=registry)
    result = checker.check(STUB_ARTIFACT_ID)
    assert result.status == HealthStatus.UNHEALTHY


@pytest.mark.unit
def test_artifact_health_checker_degraded_expired_state() -> None:
    registry = ArtifactRegistry()
    reference, metadata, manifest = make_stub_artifact_bundle()
    registry.register(metadata=metadata, manifest=manifest, reference=reference)
    registry.update_state(STUB_ARTIFACT_ID, ArtifactState.EXPIRED)
    checker = ArtifactHealthChecker(registry=registry)
    result = checker.check(STUB_ARTIFACT_ID)
    assert result.status == HealthStatus.DEGRADED

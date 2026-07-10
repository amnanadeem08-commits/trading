"""Coverage tests for storage providers."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from storage_providers import (
    HealthStatus,
    ProviderManifest,
    ProviderMetadata,
    ProviderPathError,
    ProviderResolutionError,
    ProviderType,
    ProviderValidationError,
    StorageProviderError,
    StorageProviderValidator,
    build_storage_bridge,
    create_local_provider,
)
from storage_providers.health.provider_health import ProviderHealthChecker
from storage_providers.providers.path_sandbox import (
    PathSandbox,
    PathSandboxConfig,
    parse_storage_uri,
)
from storage_providers.registry.provider_record import ProviderState
from storage_providers.registry.provider_registry import ProviderRegistry
from storage_providers.resolver.provider_resolver import ProviderResolver
from storage_providers.validation.validation_result import ProviderValidationResult
from storage_providers.versioning.provider_version import ProviderVersionRegistry
from tests.storage_providers_helpers import (
    make_local_artifact_bundle,
    make_local_storage_bridge,
    make_stub_storage_provider,
    write_test_artifact,
)

if TYPE_CHECKING:
    from pathlib import Path


@pytest.mark.unit
def test_provider_type_enum_values() -> None:
    assert ProviderType.LOCAL.value == "local"
    assert ProviderType.S3.value == "s3"
    assert ProviderType.GCS.value == "gcs"


@pytest.mark.unit
def test_provider_registry_resolve_rejects_invalid_uri() -> None:
    registry = ProviderRegistry()
    registry.register(make_stub_storage_provider())
    with pytest.raises(ProviderResolutionError):
        registry.resolve("invalid-uri")


@pytest.mark.unit
def test_provider_version_registry_get_missing() -> None:
    registry = ProviderVersionRegistry()
    with pytest.raises(StorageProviderError):
        registry.get("missing")


@pytest.mark.unit
def test_provider_resolver_manifest_mismatch() -> None:
    registry = ProviderRegistry()
    provider = make_stub_storage_provider()
    registry.register(provider)
    resolver = ProviderResolver(registry=registry)
    manifest = ProviderManifest(
        provider_id="other-provider",
        name="Other",
        version="1.0.0",
        supported_uri_schemes=("local",),
    )
    with pytest.raises(ProviderResolutionError):
        resolver.resolve("local://artifacts/model.stub", manifest=manifest)


@pytest.mark.unit
def test_validator_metadata_and_manifest_errors() -> None:
    validator = StorageProviderValidator()
    bad_metadata = ProviderMetadata(provider_id="", name="", version="")
    bad_manifest = ProviderManifest(
        provider_id="",
        name="",
        version="",
        supported_uri_schemes=(),
    )
    assert validator.validate_metadata(bad_metadata).valid is False
    assert validator.validate_manifest(bad_manifest).valid is False


@pytest.mark.unit
def test_validator_provider_type_and_id_mismatch() -> None:
    from storage_providers.contracts.provider_capability import ProviderCapability
    from storage_providers.contracts.storage_provider import StorageProvider

    class BadProvider(StorageProvider):
        def provider_id(self) -> str:
            return "bad-provider"

        def provider_type(self) -> ProviderType:
            return ProviderType.S3

        def metadata(self) -> ProviderMetadata:
            return ProviderMetadata(provider_id="bad-provider", name="Bad", version="1.0.0")

        def manifest(self) -> ProviderManifest:
            return ProviderManifest(
                provider_id="other-provider",
                name="Bad",
                version="1.0.0",
                provider_type=ProviderType.LOCAL,
                supported_uri_schemes=("local",),
                capabilities=(ProviderCapability.METADATA_RESOLUTION,),
            )

        def capabilities(self) -> tuple[ProviderCapability, ...]:
            return (ProviderCapability.METADATA_RESOLUTION,)

        def validate(self) -> dict[str, object]:
            return {"valid": True}

        def resolve(self, *, uri: str) -> dict[str, object]:
            return {"uri": uri}

        def fetch_metadata(self, *, uri: str) -> dict[str, object]:
            return {"uri": uri, "complete": True}

        def shutdown(self) -> None:
            return None

    validator = StorageProviderValidator()
    assert validator.validate_provider(BadProvider()).valid is False


@pytest.mark.unit
def test_validator_provider_healthy_and_degraded_states() -> None:
    registry = ProviderRegistry()
    provider = make_stub_storage_provider(provider_id="health-provider")
    registry.register(provider)
    validator = StorageProviderValidator(registry=registry)
    assert validator.validate_provider_healthy("health-provider").valid is True

    registry.update_state("health-provider", ProviderState.SHUTDOWN)
    checker = ProviderHealthChecker(registry=registry)
    result = checker.check("health-provider")
    assert result.status == HealthStatus.DEGRADED


@pytest.mark.unit
def test_validator_ensure_valid_and_warnings() -> None:
    validator = StorageProviderValidator()
    result = ProviderValidationResult.success(provider_id="p1").with_warnings("note")
    assert result.warnings == ("note",)
    with pytest.raises(ProviderValidationError):
        validator.ensure_valid(ProviderValidationResult.failure("bad", provider_id="p1"))


@pytest.mark.unit
def test_bridge_register_provider_validation_failure() -> None:
    bridge = build_storage_bridge(auto_register_defaults=False)
    provider = make_stub_storage_provider()
    bridge.provider_registry.register(provider)
    with pytest.raises(ProviderValidationError):
        bridge.register_provider(provider)


@pytest.mark.unit
def test_bridge_shutdown_default_providers_when_missing() -> None:
    bridge = build_storage_bridge(auto_register_defaults=False)
    bridge.shutdown_default_providers()


@pytest.mark.unit
def test_path_sandbox_rejects_empty_and_invalid_uris() -> None:
    with pytest.raises(ProviderResolutionError):
        parse_storage_uri("invalid")
    with pytest.raises(ProviderResolutionError):
        parse_storage_uri("ftp://remote/file")
    with pytest.raises(ProviderResolutionError):
        parse_storage_uri("local://")


@pytest.mark.unit
def test_path_sandbox_rejects_escape_outside_root(tmp_path: Path) -> None:
    root = tmp_path / "artifacts"
    root.mkdir()
    sandbox = PathSandbox(PathSandboxConfig(artifact_root=root))
    with pytest.raises(ProviderPathError):
        sandbox.resolve_uri_to_path("local://../../outside.txt")


@pytest.mark.unit
def test_validator_checksum_and_file_existence_failures(tmp_path: Path) -> None:
    relative = "artifacts/fail.stub"
    write_test_artifact(tmp_path, relative_path=relative, content=b"x")
    provider = create_local_provider(artifact_root=tmp_path)
    validator = StorageProviderValidator()
    assert (
        validator.validate_file_existence(
            provider=provider,
            uri="local://missing.stub",
        ).valid
        is False
    )
    assert (
        validator.validate_checksum(
            provider=provider,
            uri=f"local://{relative}",
            expected_checksum="bad-checksum",
        ).valid
        is False
    )


@pytest.mark.unit
def test_bridge_filesystem_failure_metrics(tmp_path: Path) -> None:
    bridge = make_local_storage_bridge(tmp_path)
    reference, metadata, manifest, _ = make_local_artifact_bundle(tmp_path)
    with pytest.raises(ProviderValidationError):
        bridge.resolve_through_provider(
            reference=reference.model_copy(update={"uri": "local://missing/file.stub"}),
            metadata=metadata,
            manifest=manifest,
        )
    stats = bridge.provider_metrics_collector.statistics()
    assert stats.missing_files >= 1


@pytest.mark.unit
def test_bridge_validation_failure_bad_checksum(tmp_path: Path) -> None:
    bridge = make_local_storage_bridge(tmp_path)
    reference, metadata, manifest, _ = make_local_artifact_bundle(tmp_path)
    bad_reference = reference.model_copy(
        update={"checksum": reference.checksum.model_copy(update={"value": "bad-checksum"})}
    )
    with pytest.raises(ProviderValidationError):
        bridge.resolve_through_provider(
            reference=bad_reference,
            metadata=metadata,
            manifest=manifest,
        )
    stats = bridge.provider_metrics_collector.statistics()
    assert stats.validation_failures >= 1


@pytest.mark.unit
def test_validator_file_existence_path_error(tmp_path: Path) -> None:
    provider = create_local_provider(artifact_root=tmp_path)
    validator = StorageProviderValidator()
    result = validator.validate_file_existence(
        provider=provider,
        uri="local://../outside.txt",
    )
    assert result.valid is False


@pytest.mark.unit
def test_validator_checksum_missing_from_metadata(tmp_path: Path) -> None:
    from storage_providers.contracts.provider_capability import ProviderCapability
    from storage_providers.contracts.storage_provider import StorageProvider

    class NoChecksumProvider(StorageProvider):
        def provider_id(self) -> str:
            return "no-checksum"

        def provider_type(self) -> ProviderType:
            return ProviderType.LOCAL

        def metadata(self) -> ProviderMetadata:
            return ProviderMetadata(provider_id="no-checksum", name="No Checksum", version="1.0.0")

        def manifest(self) -> ProviderManifest:
            return ProviderManifest(
                provider_id="no-checksum",
                name="No Checksum",
                version="1.0.0",
                provider_type=ProviderType.LOCAL,
                supported_uri_schemes=("local",),
                capabilities=(ProviderCapability.METADATA_RESOLUTION,),
            )

        def capabilities(self) -> tuple[ProviderCapability, ...]:
            return (ProviderCapability.METADATA_RESOLUTION,)

        def validate(self) -> dict[str, object]:
            return {"valid": True}

        def resolve(self, *, uri: str) -> dict[str, object]:
            return {"uri": uri}

        def fetch_metadata(self, *, uri: str) -> dict[str, object]:
            return {"uri": uri, "complete": True}

        def shutdown(self) -> None:
            return None

    validator = StorageProviderValidator()
    result = validator.validate_checksum(
        provider=NoChecksumProvider(),
        uri="local://test.stub",
        expected_checksum="abc",
    )
    assert result.valid is False

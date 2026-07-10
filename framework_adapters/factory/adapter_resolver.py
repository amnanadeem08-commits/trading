"""Adapter resolver."""

from __future__ import annotations

from framework_adapters.contracts.adapter_manifest import AdapterManifest
from framework_adapters.contracts.adapter_metadata import AdapterMetadata
from framework_adapters.contracts.engine_type import EngineType
from framework_adapters.contracts.framework_adapter import FrameworkAdapter
from framework_adapters.exceptions import AdapterResolutionError
from framework_adapters.factory.adapter_factory import AdapterFactory


class AdapterResolver:
    """Resolves adapters by engine type, manifest, and metadata."""

    def __init__(self, *, factory: AdapterFactory) -> None:
        self._factory = factory

    def resolve_engine_type(self, value: str) -> EngineType:
        normalized = value.strip().lower()
        try:
            return EngineType(normalized)
        except ValueError as error:
            msg = f"Unsupported engine type: {value}"
            raise AdapterResolutionError(msg) from error

    def resolve(
        self,
        *,
        engine_type: EngineType,
        manifest: AdapterManifest | None = None,
        metadata: AdapterMetadata | None = None,
    ) -> FrameworkAdapter:
        if manifest is not None and manifest.engine_type != engine_type:
            msg = "manifest.engine_type does not match requested engine_type"
            raise AdapterResolutionError(msg)
        if metadata is not None and metadata.engine_type != engine_type:
            msg = "metadata.engine_type does not match requested engine_type"
            raise AdapterResolutionError(msg)
        if (
            manifest is not None
            and metadata is not None
            and manifest.adapter_id != metadata.adapter_id
        ):
            msg = "manifest.adapter_id does not match metadata.adapter_id"
            raise AdapterResolutionError(msg)
        return self._factory.create(engine_type)

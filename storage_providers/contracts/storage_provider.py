"""Storage provider contract."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from storage_providers.contracts.provider_capability import ProviderCapability
from storage_providers.contracts.provider_manifest import ProviderManifest
from storage_providers.contracts.provider_metadata import ProviderMetadata
from storage_providers.contracts.provider_type import ProviderType


class StorageProvider(ABC):
    """Abstract interface for artifact storage backends."""

    @abstractmethod
    def provider_id(self) -> str:
        """Return the provider identifier."""

    @abstractmethod
    def provider_type(self) -> ProviderType:
        """Return the provider type."""

    @abstractmethod
    def metadata(self) -> ProviderMetadata:
        """Return provider metadata."""

    @abstractmethod
    def manifest(self) -> ProviderManifest:
        """Return provider manifest."""

    @abstractmethod
    def capabilities(self) -> tuple[ProviderCapability, ...]:
        """Return supported capabilities."""

    @abstractmethod
    def validate(self) -> dict[str, Any]:
        """Validate provider contract. No network or filesystem access."""

    @abstractmethod
    def resolve(self, *, uri: str) -> dict[str, Any]:
        """Resolve a URI into metadata-only location descriptors."""

    @abstractmethod
    def fetch_metadata(self, *, uri: str) -> dict[str, Any]:
        """Fetch resource metadata for a URI without downloading content."""

    @abstractmethod
    def shutdown(self) -> None:
        """Release provider resources."""

"""Execution adapter contracts."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from connectors.adapters.adapter_context import AdapterContext
from connectors.adapters.adapter_metadata import AdapterHealthResult, AdapterMetadata


class ExecutionAdapter(ABC):
    """Generic execution adapter contract. No external implementation."""

    @abstractmethod
    def adapter_id(self) -> str:
        """Return the unique adapter identifier."""

    @abstractmethod
    def name(self) -> str:
        """Return the human-readable adapter name."""

    @abstractmethod
    def version(self) -> str:
        """Return the adapter version."""

    def metadata(self) -> AdapterMetadata:
        """Return adapter metadata."""
        return AdapterMetadata(
            adapter_id=self.adapter_id(),
            name=self.name(),
            version=self.version(),
        )

    @abstractmethod
    def initialize(self, context: AdapterContext) -> None:
        """Prepare the adapter for dispatch operations."""

    @abstractmethod
    def validate(self, context: AdapterContext) -> bool:
        """Validate adapter readiness for the given context."""

    @abstractmethod
    def dispatch(self, context: AdapterContext) -> dict[str, Any]:
        """Process a dispatch request without performing external actions."""

    @abstractmethod
    def shutdown(self, context: AdapterContext) -> None:
        """Release adapter resources."""

    @abstractmethod
    def health(self) -> AdapterHealthResult:
        """Return current adapter health status."""

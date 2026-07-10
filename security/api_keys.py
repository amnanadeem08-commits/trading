"""API key provider interface."""

from __future__ import annotations

from abc import ABC, abstractmethod

from security.models import Identity


class ApiKeyProvider(ABC):
    """Interface for API key validation."""

    @abstractmethod
    def validate_key(self, api_key: str) -> Identity | None:
        """Validate an API key and return the associated identity."""

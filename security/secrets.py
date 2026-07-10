"""Secret provider interface."""

from __future__ import annotations

from abc import ABC, abstractmethod


class SecretProvider(ABC):
    """Interface for retrieving secrets by key."""

    @abstractmethod
    def get_secret(self, key: str) -> str | None:
        """Return secret value for key, or None if not found."""

    @abstractmethod
    def has_secret(self, key: str) -> bool:
        """Return whether a secret exists for key."""

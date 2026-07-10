"""Hash provider interface."""

from __future__ import annotations

from abc import ABC, abstractmethod


class HashProvider(ABC):
    """Interface for hashing and verifying values."""

    @abstractmethod
    def hash(self, value: str) -> str:
        """Return hash digest for value."""

    @abstractmethod
    def verify(self, value: str, digest: str) -> bool:
        """Verify value against digest."""

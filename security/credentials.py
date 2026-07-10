"""Credential provider interface."""

from __future__ import annotations

from abc import ABC, abstractmethod

from security.models import Identity


class CredentialProvider(ABC):
    """Interface for resolving credentials to identities."""

    @abstractmethod
    def resolve(self, credential: str) -> Identity | None:
        """Resolve a credential string to an identity."""

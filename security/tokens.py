"""Token provider interface."""

from __future__ import annotations

from abc import ABC, abstractmethod

from security.models import Identity


class TokenProvider(ABC):
    """Interface for token issuance and validation."""

    @abstractmethod
    def issue(self, identity: Identity) -> str:
        """Issue a token for an identity."""

    @abstractmethod
    def validate(self, token: str) -> Identity | None:
        """Validate a token and return the identity if valid."""

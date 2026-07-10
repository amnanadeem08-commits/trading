"""Dataset transformation utilities."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class DataTransformer(ABC):
    """Abstract dataset record transformer."""

    @abstractmethod
    def transform(self, records: tuple[dict[str, Any], ...]) -> tuple[dict[str, Any], ...]:
        """Transform dataset records."""

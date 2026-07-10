"""Stub environment validation for framework adapter contracts."""

from __future__ import annotations

from typing import Any

from models.common import PlatformModel


class StubEnvironment(PlatformModel):
    """Simulated environment validation. No actual inspection."""

    python_available: bool = True
    runtime_supported: bool = True
    framework_available: bool = True

    def check_environment(self) -> dict[str, Any]:
        """Return deterministic environment metadata."""
        healthy = self.python_available and self.runtime_supported and self.framework_available
        return {
            "status": "healthy" if healthy else "degraded",
            "python_available": self.python_available,
            "runtime_supported": self.runtime_supported,
            "framework_available": self.framework_available,
        }

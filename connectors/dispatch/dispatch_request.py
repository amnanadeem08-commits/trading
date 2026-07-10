"""Connector dispatch request contracts."""

from __future__ import annotations

from pydantic import Field

from execution.dispatch.dispatch_request import DispatchRequest
from models.common import PlatformModel


class ConnectorDispatchRequest(PlatformModel):
    """Connector-layer view of an execution dispatch request."""

    adapter_id: str = Field(min_length=1)
    request: DispatchRequest

"""Prompt template contracts."""

from __future__ import annotations

import re
from typing import Any

from pydantic import Field

from models.common import PlatformModel

_VARIABLE_PATTERN = re.compile(r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}")


class PromptTemplate(PlatformModel):
    """Template prompt with variable injection support."""

    template_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    version: str = Field(min_length=1)
    template: str = Field(min_length=1)
    variables: tuple[str, ...] = Field(default_factory=tuple)
    description: str = ""

    def render(self, values: dict[str, Any]) -> str:
        """Render the template with provided variable values."""
        rendered = self.template
        for variable in self.variables:
            if variable not in values:
                msg = f"Missing template variable: {variable}"
                raise KeyError(msg)
            rendered = rendered.replace(f"{{{variable}}}", str(values[variable]))
        return rendered

    @classmethod
    def from_template(
        cls,
        *,
        template_id: str,
        name: str,
        version: str,
        template: str,
        description: str = "",
    ) -> PromptTemplate:
        """Create a template and extract variable names."""
        variables = tuple(sorted(set(_VARIABLE_PATTERN.findall(template))))
        return cls(
            template_id=template_id,
            name=name,
            version=version,
            template=template,
            variables=variables,
            description=description,
        )

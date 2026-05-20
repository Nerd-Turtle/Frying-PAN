from __future__ import annotations

from pydantic import BaseModel, Field


class ApplicationSet(BaseModel):
    values: set[str] = Field(default_factory=lambda: {"any"})
    negated: bool = False

    def contains(self, value: str) -> bool:
        return "any" in self.values or value in self.values

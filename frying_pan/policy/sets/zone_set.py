from __future__ import annotations

from pydantic import BaseModel, Field


class ZoneSet(BaseModel):
    values: set[str] = Field(default_factory=lambda: {"any"})
    negated: bool = False

    def contains(self, value: str) -> bool:
        return "any" in self.values or value in self.values

    def overlaps(self, other: ZoneSet) -> bool:
        return "any" in self.values or "any" in other.values or bool(self.values & other.values)

from __future__ import annotations

from pydantic import BaseModel, Field


class ServiceCriterion(BaseModel):
    protocol: str
    destination_port: int | None = None


class ServiceSet(BaseModel):
    values: set[str] = Field(default_factory=lambda: {"any"})
    negated: bool = False

    def contains(self, service: str) -> bool:
        return "any" in self.values or service in self.values

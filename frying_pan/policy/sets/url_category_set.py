from __future__ import annotations

from pydantic import BaseModel, Field


class UrlCategorySet(BaseModel):
    values: set[str] = Field(default_factory=set)
    negated: bool = False

    def contains(self, value: str | None) -> bool:
        if not self.values:
            return True
        return value in self.values

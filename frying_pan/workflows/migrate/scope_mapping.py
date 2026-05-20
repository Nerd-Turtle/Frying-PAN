from __future__ import annotations

from pydantic import BaseModel


class ScopeMapping(BaseModel):
    source_scope_path: str
    target_scope_path: str
    notes: str | None = None

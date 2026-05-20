from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel


class ObjectMappingMode(StrEnum):
    COPY = "copy"
    REUSE_TARGET = "reuse_target"
    RENAME_AND_COPY = "rename_and_copy"
    SKIP = "skip"


class ObjectMapping(BaseModel):
    source_object_ref: str
    target_object_ref: str | None = None
    mode: ObjectMappingMode = ObjectMappingMode.COPY

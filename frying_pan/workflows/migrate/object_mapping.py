from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field, model_validator


class ObjectMappingMode(StrEnum):
    COPY = "copy"
    REUSE_TARGET = "reuse_target"
    RENAME_AND_COPY = "rename_and_copy"
    MERGE = "merge"
    SKIP = "skip"


class ObjectMapping(BaseModel):
    source_object_ref: str
    target_object_ref: str | None = None
    mode: ObjectMappingMode = ObjectMappingMode.COPY
    warnings: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _validate_target_ref(self) -> ObjectMapping:
        if self.mode in {
            ObjectMappingMode.REUSE_TARGET,
            ObjectMappingMode.RENAME_AND_COPY,
            ObjectMappingMode.MERGE,
        } and not self.target_object_ref:
            raise ValueError(f"{self.mode.value} requires target_object_ref.")
        return self

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from frying_pan.workflows.convert.converted_import import ConvertedImportPackage


class ConversionAdapter(ABC):
    source_format: str

    @abstractmethod
    def can_parse(self, path: Path) -> bool:
        """Return whether this adapter can parse the local source file."""

    @abstractmethod
    def convert(self, path: Path) -> ConvertedImportPackage:
        """Convert a local source file into a normalized import package."""

from __future__ import annotations

from abc import ABC

from frying_pan.sources.base import SourceAdapter


class VendorImportAdapter(SourceAdapter, ABC):
    """Base class for future non-Palo Alto source adapters."""

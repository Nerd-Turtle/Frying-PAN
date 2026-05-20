from __future__ import annotations

from frying_pan.normalized.config import NormalizedConfig
from frying_pan.sources.base import SourceConfig, SourceType
from frying_pan.sources.vendor_base import VendorImportAdapter


class FutureVendorImportAdapter(VendorImportAdapter):
    source_type = SourceType.VENDOR_IMPORT_FUTURE

    def parse(self, source: SourceConfig) -> NormalizedConfig:
        return NormalizedConfig(
            source_id=source.id,
            source_type=source.source_type,
            warnings=["Vendor conversion adapters are planned for a later MVP."],
        )

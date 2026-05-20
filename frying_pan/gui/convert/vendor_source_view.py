from __future__ import annotations

from frying_pan.gui.placeholders import PlaceholderView


class VendorSourceView(PlaceholderView):
    def __init__(self) -> None:
        super().__init__("Vendor Source", "Future non-Palo Alto source parsing and review.")

from __future__ import annotations

from frying_pan.gui.placeholders import PlaceholderView


class ConversionMappingView(PlaceholderView):
    def __init__(self) -> None:
        super().__init__(
            "Conversion Warnings", "Lossy or unsupported conversion decisions will be staged here."
        )

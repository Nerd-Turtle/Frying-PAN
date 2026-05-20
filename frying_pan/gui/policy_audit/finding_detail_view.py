from __future__ import annotations

from frying_pan.gui.placeholders import PlaceholderView


class FindingDetailView(PlaceholderView):
    def __init__(self) -> None:
        super().__init__(
            "Finding Details", "Finding explanation and rule comparison will appear here."
        )

from __future__ import annotations

from frying_pan.gui.placeholders import PlaceholderView


class ReportView(PlaceholderView):
    def __init__(self) -> None:
        super().__init__(
            "Reports",
            "Markdown and HTML report exports will appear here before XML export support.",
        )

from __future__ import annotations

from frying_pan.gui.placeholders import PlaceholderView


class MatchTraceView(PlaceholderView):
    def __init__(self) -> None:
        super().__init__(
            "Evaluation Trace", "Skipped rules, first match, later matches, and warnings."
        )

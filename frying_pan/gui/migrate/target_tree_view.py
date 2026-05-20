from __future__ import annotations

from frying_pan.gui.placeholders import PlaceholderView


class TargetTreeView(PlaceholderView):
    def __init__(self) -> None:
        super().__init__(
            "Target Config Tree", "Drop onto target scopes to create staged plan decisions."
        )

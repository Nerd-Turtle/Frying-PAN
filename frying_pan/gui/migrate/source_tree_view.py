from __future__ import annotations

from frying_pan.gui.placeholders import PlaceholderView


class SourceTreeView(PlaceholderView):
    def __init__(self) -> None:
        super().__init__(
            "Source Config Tree",
            "Drag source objects or rules from here to stage migration decisions.",
        )

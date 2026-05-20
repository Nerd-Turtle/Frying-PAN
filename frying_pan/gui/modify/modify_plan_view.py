from __future__ import annotations

from frying_pan.gui.placeholders import PlaceholderView


class ModifyPlanView(PlaceholderView):
    def __init__(self) -> None:
        super().__init__(
            "Planned Modifications",
            "Object moves, renames, dedupe actions, and rule ordering changes will be staged here.",
        )

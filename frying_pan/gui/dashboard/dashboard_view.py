from __future__ import annotations

from frying_pan.gui.placeholders import PlaceholderView


class DashboardView(PlaceholderView):
    def __init__(self) -> None:
        super().__init__(
            "Dashboard",
            "Open or create a local Frying-PAN project workspace, "
            "then import configuration sources.",
        )

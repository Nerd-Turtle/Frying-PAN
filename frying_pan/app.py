from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from frying_pan.gui.main_window import MainWindow
from frying_pan.gui.theme import apply_application_theme


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Frying-PAN")
    app.setApplicationDisplayName("Frying-PAN")
    app.setOrganizationName("Frying-PAN")
    app.setOrganizationDomain("frying-pan.local")
    apply_application_theme(app)

    window = MainWindow()
    window.resize(1440, 900)
    window.show()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())

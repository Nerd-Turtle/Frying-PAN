from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from frying_pan.gui.main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Frying-PAN")
    app.setOrganizationName("Frying-PAN")

    window = MainWindow()
    window.resize(1280, 820)
    window.show()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())

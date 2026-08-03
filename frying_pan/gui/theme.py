from __future__ import annotations

import os
import sys
from pathlib import Path

from PySide6.QtGui import QColor, QFont, QFontDatabase, QPalette
from PySide6.QtWidgets import QApplication

WORKBENCH_STYLESHEET = """
QWidget {
    color: #d8dee9;
    font-family: "Segoe UI", "Inter", sans-serif;
    font-size: 10pt;
}

QMainWindow, QWidget#WorkbenchRoot, QStackedWidget#WorkbenchStack {
    background: #171a21;
}

QMenuBar {
    background: #20242d;
    border-bottom: 1px solid #303642;
    padding: 2px;
}

QMenuBar::item {
    background: transparent;
    padding: 5px 10px;
}

QMenuBar::item:selected, QMenu::item:selected {
    background: #343b49;
}

QMenu {
    background: #252a34;
    border: 1px solid #3b4352;
    padding: 4px;
}

QMenu::item {
    padding: 7px 28px 7px 24px;
}

QToolBar#WorkbenchToolbar {
    background: #20242d;
    border: 0;
    border-bottom: 1px solid #303642;
    spacing: 5px;
    padding: 5px 8px;
}

QToolBar#WorkbenchToolbar QToolButton {
    background: transparent;
    border: 1px solid transparent;
    border-radius: 4px;
    padding: 5px 8px;
}

QToolBar#WorkbenchToolbar QToolButton:hover {
    background: #303642;
    border-color: #3b4352;
}

QLineEdit#CommandCenter {
    background: #2a2f3a;
    border: 1px solid #444d5d;
    border-radius: 5px;
    color: #e7ebf1;
    padding: 5px 10px;
    min-width: 280px;
}

QListWidget#ActivityNavigation {
    background: #1d2129;
    border: 0;
    border-right: 1px solid #303642;
    outline: 0;
    padding: 7px 0;
}

QListWidget#ActivityNavigation::item {
    border-left: 3px solid transparent;
    color: #9da7b7;
    min-height: 38px;
    padding: 4px 8px;
}

QListWidget#ActivityNavigation::item:hover {
    background: #272c36;
    color: #f2f4f8;
}

QListWidget#ActivityNavigation::item:selected {
    background: #2a303b;
    border-left-color: #ef8354;
    color: #ffffff;
}

QWidget#ProjectExplorer {
    background: #20242d;
    border-right: 1px solid #303642;
}

QLabel#SidebarHeading {
    color: #8993a4;
    font-size: 8pt;
    font-weight: 600;
    letter-spacing: 1px;
}

QLabel#ProjectHeading {
    color: #eef1f6;
    font-size: 9pt;
    font-weight: 700;
}

QLabel#MutedCopy, QLabel[muted="true"] {
    color: #8f99a9;
}

QTreeWidget#ProjectTree {
    background: transparent;
    border: 0;
    outline: 0;
}

QTreeWidget#ProjectTree::item {
    min-height: 24px;
    padding: 2px 4px;
}

QTreeWidget#ProjectTree::item:hover {
    background: #2b303b;
}

QTreeWidget#ProjectTree::item:selected {
    background: #354052;
}

QTabWidget::pane {
    border: 1px solid #303642;
    background: #171a21;
    top: -1px;
}

QTabWidget QTabBar::tab {
    background: #20242d;
    border: 1px solid #303642;
    color: #939dad;
    min-width: 110px;
    padding: 8px 14px;
}

QTabWidget QTabBar::tab:hover {
    color: #f0f2f6;
}

QTabWidget QTabBar::tab:selected {
    background: #171a21;
    border-bottom-color: #171a21;
    border-top: 2px solid #ef8354;
    color: #ffffff;
    padding-top: 7px;
}

QStatusBar {
    background: #b54428;
    color: #ffffff;
    border: 0;
}

QStatusBar QLabel {
    color: #ffffff;
    padding: 0 8px;
}

QSplitter::handle {
    background: #303642;
    width: 1px;
    height: 1px;
}

QPushButton {
    background: #333a47;
    border: 1px solid #465062;
    border-radius: 4px;
    color: #eef1f6;
    min-height: 26px;
    padding: 3px 10px;
}

QPushButton:hover {
    background: #3d4655;
    border-color: #647187;
}

QPushButton:pressed {
    background: #2b313c;
}

QPushButton:disabled {
    background: #252a33;
    border-color: #333945;
    color: #697384;
}

QPushButton[primary="true"] {
    background: #c95634;
    border-color: #df6945;
    font-weight: 600;
}

QPushButton[primary="true"]:hover {
    background: #dd6540;
}

QLabel#PageTitle {
    color: #f4f6f9;
    font-size: 22pt;
    font-weight: 600;
}

QLabel#PageSubtitle {
    color: #9ba6b6;
    font-size: 10.5pt;
}

QFrame#WorkbenchCard {
    background: #20242d;
    border: 1px solid #303642;
    border-radius: 7px;
}

QLabel#CardHeading {
    color: #edf0f5;
    font-size: 12pt;
    font-weight: 600;
}

QLabel#MetricValue {
    color: #ffffff;
    font-size: 20pt;
    font-weight: 600;
}

QLabel#ProjectPathPreview {
    background: #171a21;
    border: 1px solid #303642;
    border-radius: 4px;
    color: #e5e9f0;
    padding: 9px;
}

QLabel#ValidationMessage {
    color: #e6a37c;
    min-height: 20px;
}

QLabel#ValidationMessage[valid="true"] {
    color: #8fc49b;
}

QTableWidget, QTableView {
    alternate-background-color: #1d2129;
    background: #171a21;
    border: 1px solid #303642;
    gridline-color: #303642;
    selection-background-color: #354052;
    selection-color: #ffffff;
}

QTableWidget::item, QTableView::item {
    padding: 5px;
}

QHeaderView::section {
    background: #252a34;
    border: 0;
    border-bottom: 1px solid #3a414e;
    border-right: 1px solid #303642;
    color: #acb5c3;
    font-weight: 600;
    padding: 7px;
}

QLineEdit, QComboBox, QSpinBox {
    background: #1d2129;
    border: 1px solid #414a59;
    border-radius: 4px;
    color: #edf0f5;
    min-height: 27px;
    padding: 2px 7px;
}

QLineEdit:focus, QComboBox:focus, QSpinBox:focus {
    border-color: #e16b46;
}

QComboBox QAbstractItemView {
    background: #252a34;
    border: 1px solid #414a59;
    selection-background-color: #354052;
}

QScrollBar:vertical {
    background: #171a21;
    border: 0;
    width: 12px;
}

QScrollBar::handle:vertical {
    background: #454e5e;
    border-radius: 5px;
    min-height: 28px;
    margin: 2px;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: transparent;
    height: 0;
}

QToolTip {
    background: #303642;
    border: 1px solid #596477;
    color: #f4f6f9;
    padding: 4px;
}
"""


def apply_application_theme(app: QApplication) -> None:
    app.setStyle("Fusion")
    _configure_application_font(app)
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor("#171a21"))
    palette.setColor(QPalette.ColorRole.WindowText, QColor("#d8dee9"))
    palette.setColor(QPalette.ColorRole.Base, QColor("#171a21"))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#1d2129"))
    palette.setColor(QPalette.ColorRole.Text, QColor("#d8dee9"))
    palette.setColor(QPalette.ColorRole.Button, QColor("#333a47"))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor("#eef1f6"))
    palette.setColor(QPalette.ColorRole.Highlight, QColor("#b54428"))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
    palette.setColor(QPalette.ColorRole.PlaceholderText, QColor("#758093"))
    app.setPalette(palette)
    app.setStyleSheet(WORKBENCH_STYLESHEET)


def _configure_application_font(app: QApplication) -> None:
    """Keep text legible when Qt's Windows font discovery is unavailable."""

    preferred_family = "Segoe UI"
    if sys.platform == "win32" and preferred_family not in QFontDatabase.families():
        windows_root = Path(os.environ.get("WINDIR", r"C:\Windows"))
        font_path = windows_root / "Fonts" / "segoeui.ttf"
        if font_path.is_file():
            QFontDatabase.addApplicationFont(str(font_path))
    if preferred_family in QFontDatabase.families():
        app.setFont(QFont(preferred_family, 10))

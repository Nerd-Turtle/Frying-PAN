from __future__ import annotations

from PySide6.QtWidgets import QFormLayout, QLineEdit, QWidget

from frying_pan.policy.match.test_case import PolicyTestCase


class FlowInputForm(QWidget):
    def __init__(self) -> None:
        super().__init__()
        layout = QFormLayout(self)
        self.source_zone = QLineEdit()
        self.destination_zone = QLineEdit()
        self.source_ip = QLineEdit()
        self.destination_ip = QLineEdit()
        self.protocol = QLineEdit()
        self.destination_port = QLineEdit()
        self.source_port = QLineEdit()
        self.application = QLineEdit("any")
        self.user = QLineEdit("any")
        self.url_category = QLineEdit()
        for label, widget in (
            ("Source zone", self.source_zone),
            ("Destination zone", self.destination_zone),
            ("Source IP", self.source_ip),
            ("Destination IP", self.destination_ip),
            ("Protocol", self.protocol),
            ("Destination port", self.destination_port),
            ("Source port", self.source_port),
            ("Application", self.application),
            ("User", self.user),
            ("URL category", self.url_category),
        ):
            layout.addRow(label, widget)

    def to_test_case(self) -> PolicyTestCase:
        return PolicyTestCase(
            source_zone=self.source_zone.text(),
            destination_zone=self.destination_zone.text(),
            source_ip=self.source_ip.text(),
            destination_ip=self.destination_ip.text(),
            protocol=self.protocol.text(),
            destination_port=_optional_port(self.destination_port.text()),
            source_port=_optional_port(self.source_port.text()),
            application=self.application.text() or "any",
            user=self.user.text() or "any",
            url_category=self.url_category.text() or None,
        )


def _optional_port(value: str) -> int | None:
    stripped = value.strip()
    return int(stripped) if stripped else None

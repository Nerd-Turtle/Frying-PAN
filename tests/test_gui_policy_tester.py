from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from frying_pan.gui.policy_tester.flow_input_form import FlowInputForm
from frying_pan.gui.policy_tester.tester_workspace import PolicyTesterWorkspace
from frying_pan.normalized.rules import RuleAction, SecurityRule
from frying_pan.policy.match.match_engine import PolicyMatchEngine
from frying_pan.policy.match.test_case import PolicyTestCase


def _app() -> QApplication:
    app = QApplication.instance()
    return app if app is not None else QApplication([])


def test_policy_tester_flow_form_builds_test_case() -> None:
    _app()
    form = FlowInputForm()
    form.source_zone.setText("trust")
    form.destination_zone.setText("untrust")
    form.source_ip.setText("192.0.2.1")
    form.destination_ip.setText("198.51.100.10")
    form.protocol.setText("tcp")
    form.destination_port.setText("443")

    test_case = form.to_test_case()

    assert test_case.destination_port == 443
    assert test_case.application == "any"


def test_policy_tester_workspace_displays_result_trace() -> None:
    _app()
    workspace = PolicyTesterWorkspace()
    test_case = PolicyTestCase(
        source_zone="trust",
        destination_zone="untrust",
        source_ip="192.0.2.1",
        destination_ip="198.51.100.10",
        protocol="tcp",
        destination_port=443,
    )
    result = PolicyMatchEngine().evaluate(
        [
            SecurityRule(
                name="allow-web",
                scope_path="shared",
                position=1,
                action=RuleAction.ALLOW,
            )
        ],
        test_case,
    )

    workspace.set_result(result)

    assert "allow-web" in workspace.result_label.text()
    assert workspace.trace_view.rowCount() == 1

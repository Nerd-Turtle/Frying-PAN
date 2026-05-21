from __future__ import annotations

from pathlib import Path

from frying_pan.cli.main import main

FIXTURES = Path(__file__).parent / "fixtures"


def test_cli_inventory_json_for_panorama_fixture(capsys) -> None:
    result = main(
        [
            "inventory",
            str(FIXTURES / "panorama" / "reference_config_items.xml"),
            "--json",
        ]
    )

    captured = capsys.readouterr()

    assert result == 0
    assert '"source_type": "panorama_xml"' in captured.out
    assert '"security_rule_count": 5' in captured.out


def test_cli_inventory_summary_and_report_for_firewall_fixture(tmp_path: Path, capsys) -> None:
    report_path = tmp_path / "inventory.md"
    result = main(
        [
            "inventory",
            str(FIXTURES / "firewall" / "reference_config_items_virtual_router.xml"),
            "--report-md",
            str(report_path),
        ]
    )

    captured = capsys.readouterr()

    assert result == 0
    assert "Source type: firewall_xml" in captured.out
    assert report_path.exists()
    assert "XML mutation/export remains blocked" in report_path.read_text(encoding="utf-8")


def test_cli_inventory_returns_nonzero_for_invalid_xml(capsys) -> None:
    result = main(["inventory", str(FIXTURES / "invalid" / "broken.xml")])

    captured = capsys.readouterr()

    assert result == 1
    assert "Cannot parse" in captured.err


def test_cli_policy_test_json_and_markdown_report(tmp_path: Path, capsys) -> None:
    report_path = tmp_path / "policy-test.md"
    result = main(
        [
            "policy-test",
            str(FIXTURES / "firewall" / "reference_config_items_virtual_router.xml"),
            "--scope",
            "vsys/vsys1",
            "--src-zone",
            "FP-REF-FW-ZONE-TRUST",
            "--dst-zone",
            "FP-REF-FW-ZONE-DMZ",
            "--src-ip",
            "10.60.10.10",
            "--dst-ip",
            "10.70.10.10",
            "--protocol",
            "tcp",
            "--dst-port",
            "443",
            "--application",
            "web-browsing",
            "--url-category",
            "FP-REF-FW-URLCAT-EXAMPLE",
            "--json",
            "--report-md",
            str(report_path),
        ]
    )

    captured = capsys.readouterr()

    assert result == 0
    assert '"action": "allow"' in captured.out
    assert "FP-REF-FW-ALLOW-USERS-TO-DMZ-WEB" in captured.out
    assert "Matched rule: `FP-REF-FW-ALLOW-USERS-TO-DMZ-WEB`" in report_path.read_text(
        encoding="utf-8"
    )


def test_cli_policy_audit_json_and_markdown_report(tmp_path: Path, capsys) -> None:
    report_path = tmp_path / "policy-audit.md"
    result = main(
        [
            "policy-audit",
            str(FIXTURES / "firewall" / "reference_config_items_virtual_router.xml"),
            "--scope",
            "vsys/vsys1",
            "--json",
            "--report-md",
            str(report_path),
        ]
    )

    captured = capsys.readouterr()

    assert result == 0
    assert '"finding_count"' in captured.out
    assert "DISABLED_RULE" in captured.out
    assert "Frying-PAN Policy Audit Report" in report_path.read_text(encoding="utf-8")

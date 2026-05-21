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


def test_cli_dedupe_analysis_json_and_markdown_report(tmp_path: Path, capsys) -> None:
    report_path = tmp_path / "dedupe.md"
    result = main(
        [
            "dedupe-analysis",
            str(FIXTURES / "panorama" / "reference_config_items.xml"),
            "--json",
            "--report-md",
            str(report_path),
        ]
    )

    captured = capsys.readouterr()

    assert result == 0
    assert '"finding_count"' in captured.out
    assert "unused_object_candidate" in captured.out
    assert "Frying-PAN Dedupe And Conflict Analysis" in report_path.read_text(
        encoding="utf-8"
    )


def test_cli_modify_plan_json_and_markdown_report(tmp_path: Path, capsys) -> None:
    report_path = tmp_path / "modify.md"
    result = main(
        [
            "modify-plan",
            str(FIXTURES / "firewall" / "reference_config_items_virtual_router.xml"),
            "--reorder-rule",
            "vsys/vsys1",
            "security_local",
            "FP-REF-FW-DROP-CLEANUP",
            "1",
            "--json",
            "--report-md",
            str(report_path),
        ]
    )

    captured = capsys.readouterr()

    assert result == 0
    assert '"action_count": 1' in captured.out
    assert "reorder_rule" in captured.out
    assert "Frying-PAN Modify Plan" in report_path.read_text(encoding="utf-8")


def test_cli_migrate_plan_json_and_markdown_report(tmp_path: Path, capsys) -> None:
    report_path = tmp_path / "migration.md"
    fixture = FIXTURES / "firewall" / "reference_config_items_virtual_router.xml"
    result = main(
        [
            "migrate-plan",
            str(fixture),
            str(fixture),
            "--map-scope",
            "vsys/vsys1",
            "vsys/vsys1",
            "--place-rule",
            "vsys/vsys1::security_local::FP-REF-FW-ALLOW-USERS-TO-DMZ-WEB",
            "vsys/vsys1::security_local",
            "append",
            "--json",
            "--report-md",
            str(report_path),
        ]
    )

    captured = capsys.readouterr()

    assert result == 0
    assert '"mapping_count": 2' in captured.out
    assert "place_rule" in captured.out
    assert "Frying-PAN Migration Plan" in report_path.read_text(encoding="utf-8")


def test_cli_convert_json_and_markdown_report(tmp_path: Path, capsys) -> None:
    report_path = tmp_path / "conversion.md"
    result = main(
        [
            "convert",
            str(FIXTURES / "vendor_future" / "generic_import.json"),
            "--format",
            "generic-json",
            "--json",
            "--report-md",
            str(report_path),
        ]
    )

    captured = capsys.readouterr()

    assert result == 0
    assert '"source_format": "generic-json"' in captured.out
    assert '"security_rule_count": 1' in captured.out
    assert "dynamic_address_group" in captured.out
    assert "Frying-PAN Conversion Report" in report_path.read_text(encoding="utf-8")


def test_cli_convert_returns_nonzero_for_invalid_package(
    tmp_path: Path, capsys
) -> None:
    source_path = tmp_path / "invalid.json"
    source_path.write_text("{}", encoding="utf-8")

    result = main(["convert", str(source_path)])

    captured = capsys.readouterr()

    assert result == 1
    assert "at least one scope" in captured.err

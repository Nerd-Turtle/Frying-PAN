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

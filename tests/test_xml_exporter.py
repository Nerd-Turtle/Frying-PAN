from __future__ import annotations

import pytest

from frying_pan.export.xml_exporter import XmlExportNotReadyError, export_xml


def test_xml_export_is_intentionally_blocked() -> None:
    with pytest.raises(XmlExportNotReadyError):
        export_xml()

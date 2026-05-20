from __future__ import annotations

from frying_pan.export.xml_exporter import XmlExportNotReadyError


def serialize_firewall_xml() -> bytes:
    raise XmlExportNotReadyError("Firewall XML serialization is not implemented yet.")

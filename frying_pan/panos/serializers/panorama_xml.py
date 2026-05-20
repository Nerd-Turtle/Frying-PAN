from __future__ import annotations

from frying_pan.export.xml_exporter import XmlExportNotReadyError


def serialize_panorama_xml() -> bytes:
    raise XmlExportNotReadyError("Panorama XML serialization is not implemented yet.")

from __future__ import annotations


class XmlExportNotReadyError(RuntimeError):
    """Raised when callers request XML export before serializer validation exists."""


def export_xml() -> None:
    raise XmlExportNotReadyError(
        "XML export is intentionally disabled until parser/serializer tests are reliable."
    )

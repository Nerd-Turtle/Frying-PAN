from __future__ import annotations

import hashlib
from pathlib import Path

from lxml import etree

from frying_pan.sources.base import SourceDetectionResult, SourceType


def checksum_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def detect_source(path: Path) -> SourceDetectionResult:
    suffix = path.suffix.lower()
    if suffix in {".json", ".yaml", ".yml"}:
        return SourceDetectionResult(
            source_type=SourceType.NORMALIZED_IMPORT_FUTURE,
            warnings=["Normalized import package detection is reserved for a future MVP."],
        )

    if suffix not in {".xml", ".pan", ".conf", ""}:
        return SourceDetectionResult(
            source_type=SourceType.VENDOR_IMPORT_FUTURE,
            warnings=["Vendor import adapters are planned but not implemented yet."],
        )

    try:
        parser = etree.XMLParser(resolve_entities=False, no_network=True, recover=False)
        root = etree.parse(str(path), parser).getroot()
    except (OSError, etree.XMLSyntaxError) as exc:
        return SourceDetectionResult(
            source_type=SourceType.UNKNOWN,
            warnings=[f"Source could not be parsed as XML: {exc}"],
        )

    if root.tag != "config":
        return SourceDetectionResult(
            source_type=SourceType.UNKNOWN,
            warnings=[f"Unsupported XML root element: {root.tag!r}"],
        )

    panos_version = root.get("version") or root.get("panos-version")
    # PAN-OS XML/XPath layouts are documented by Palo Alto Networks and summarized
    # in docs/panos-xml-notes.md for the specific parser paths Frying-PAN supports.
    # Ref: https://docs.paloaltonetworks.com/pan-os/11-0/pan-os-panorama-api/about-the-pan-os-xml-api/structure-of-a-pan-os-xml-api-request/xml-and-xpath
    has_shared_scope = bool(root.xpath("./shared"))
    supports_device_groups = bool(root.xpath("./devices/entry/device-group/entry"))
    has_vsys = bool(root.xpath("./devices/entry/vsys/entry"))
    has_templates = bool(root.xpath("./devices/entry/template/entry"))
    has_template_stacks = bool(root.xpath("./devices/entry/template-stack/entry"))

    warnings: list[str] = []
    if supports_device_groups:
        source_type = SourceType.PANORAMA_XML
        if has_vsys:
            warnings.append(
                "PAN-OS XML has both Device Group and firewall-style vsys layout; "
                "using Panorama parser selection."
            )
    elif has_vsys:
        source_type = SourceType.FIREWALL_XML
    else:
        source_type = SourceType.UNKNOWN_PANOS_XML

    if source_type == SourceType.UNKNOWN_PANOS_XML:
        warnings.append(
            "PAN-OS XML was detected, but this pass could not identify Panorama or firewall layout."
        )

    return SourceDetectionResult(
        source_type=source_type,
        panos_version=panos_version,
        has_shared_scope=has_shared_scope,
        supports_device_groups=supports_device_groups,
        has_vsys=has_vsys,
        has_templates=has_templates,
        has_template_stacks=has_template_stacks,
        warnings=warnings,
    )

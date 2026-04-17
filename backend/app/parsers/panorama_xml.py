class PanoramaXmlParser:
    """
    Placeholder parser boundary for Panorama / PAN-OS XML imports.

    TODO:
    - Parse uploaded XML into internal canonical models.
    - Separate raw XML structure from normalized object semantics.
    - Avoid scattering XML traversal logic across API routes and services.
    """

    def parse(self, xml_bytes: bytes) -> None:
        raise NotImplementedError(
            "TODO: implement Panorama XML parsing into canonical backend models."
        )

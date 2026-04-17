from app.parsers.panorama_xml import PanoramaXmlParser
from app.services.reference_service import (
    ReferenceResolutionSettings,
    resolve_references,
)


def test_example_xml_reference_resolution_distinguishes_local_shared_and_builtin() -> None:
    xml_bytes = open("/opt/frying-pan/Example-1.xml", "rb").read()
    parse_result = PanoramaXmlParser().parse(xml_bytes)

    resolved = resolve_references(
        scopes=parse_result.scopes,
        objects=parse_result.objects,
        references=parse_result.references,
    )

    dg1_group = next(
        reference
        for reference in resolved
        if reference.owner_object_name == "DG1-Group"
        and reference.target_name == "DG1-IP-Netmask"
    )
    assert dg1_group.resolution_status == "resolved_local"
    assert dg1_group.resolved_scope_path == "shared/device-group:Device-Group-1"

    nested_shared = next(
        reference
        for reference in resolved
        if reference.owner_object_name == "Nested-Groups"
        and reference.target_name == "Shared-Group"
    )
    assert nested_shared.resolution_status == "resolved_in_shared"
    assert nested_shared.resolved_scope_path == "shared"

    builtin_reference = next(
        reference
        for reference in resolved
        if reference.owner_object_name == "Shared-Service-Group"
    )
    assert builtin_reference.resolution_status == "builtin"
    assert builtin_reference.resolved_builtin_key == "service-http"


def test_reference_resolution_marks_unresolved_and_ambiguous_explicitly() -> None:
    xml_bytes = b"""
    <config version="11.2.0">
      <shared>
        <address>
          <entry name="Thing"><ip-netmask>10.0.0.1/32</ip-netmask></entry>
        </address>
        <address-group>
          <entry name="Thing"><static><member>Thing</member></static></entry>
          <entry name="Needs-Missing"><static><member>Missing-Address</member></static></entry>
          <entry name="Needs-Ambiguous"><static><member>Thing</member></static></entry>
        </address-group>
      </shared>
    </config>
    """
    parse_result = PanoramaXmlParser().parse(xml_bytes)
    resolved = resolve_references(
        scopes=parse_result.scopes,
        objects=parse_result.objects,
        references=parse_result.references,
    )

    unresolved = next(
        reference for reference in resolved if reference.owner_object_name == "Needs-Missing"
    )
    assert unresolved.resolution_status == "unresolved"

    ambiguous = next(
        reference
        for reference in resolved
        if reference.owner_object_name == "Needs-Ambiguous"
    )
    assert ambiguous.resolution_status == "ambiguous"
    assert set(ambiguous.metadata["candidate_types"]) == {"address", "address_group"}


def test_reference_resolution_precedence_is_configurable() -> None:
    xml_bytes = b"""
    <config version="11.2.0">
      <shared>
        <address />
      </shared>
      <devices>
        <entry name="localhost.localdomain">
          <device-group>
            <entry name="Parent-DG">
              <address>
                <entry name="Shared-Name"><ip-netmask>10.0.0.1/32</ip-netmask></entry>
              </address>
            </entry>
            <entry name="Child-DG">
              <address>
                <entry name="Shared-Name"><ip-netmask>10.0.0.2/32</ip-netmask></entry>
              </address>
              <address-group>
                <entry name="Chooser">
                  <static><member>Shared-Name</member></static>
                </entry>
              </address-group>
            </entry>
          </device-group>
        </entry>
      </devices>
      <readonly>
        <devices>
          <entry name="localhost.localdomain">
            <device-group>
              <entry name="Parent-DG"><id>11</id></entry>
              <entry name="Child-DG"><id>12</id><parent-dg>Parent-DG</parent-dg></entry>
            </device-group>
          </entry>
        </devices>
      </readonly>
    </config>
    """
    parse_result = PanoramaXmlParser().parse(xml_bytes)

    local_first = resolve_references(
        scopes=parse_result.scopes,
        objects=parse_result.objects,
        references=parse_result.references,
        settings=ReferenceResolutionSettings(device_group_precedence="local_first"),
    )
    ancestor_first = resolve_references(
        scopes=parse_result.scopes,
        objects=parse_result.objects,
        references=parse_result.references,
        settings=ReferenceResolutionSettings(device_group_precedence="ancestor_first"),
    )

    local_choice = next(
        reference for reference in local_first if reference.owner_object_name == "Chooser"
    )
    ancestor_choice = next(
        reference for reference in ancestor_first if reference.owner_object_name == "Chooser"
    )

    assert local_choice.resolution_status == "resolved_local"
    assert local_choice.resolved_scope_path == (
        "shared/device-group:Parent-DG/device-group:Child-DG"
    )
    assert ancestor_choice.resolution_status == "resolved_in_ancestor"
    assert ancestor_choice.resolved_scope_path == "shared/device-group:Parent-DG"

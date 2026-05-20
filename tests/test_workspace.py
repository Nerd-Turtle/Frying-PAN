from __future__ import annotations

from pathlib import Path

from frying_pan.sources.base import SourceType
from frying_pan.storage.workspace import MANIFEST_NAME, ProjectWorkspace

FIXTURES = Path(__file__).parent / "fixtures"


def test_workspace_create_and_import_source(tmp_path: Path) -> None:
    workspace = ProjectWorkspace.create(tmp_path / "Frying-PAN-Project", "Lab")
    source = workspace.import_source(FIXTURES / "panorama" / "basic_panorama.xml")

    assert workspace.manifest_path.name == MANIFEST_NAME
    assert source.source_type == SourceType.PANORAMA_XML
    assert source.workspace_path is not None
    assert source.workspace_path.exists()

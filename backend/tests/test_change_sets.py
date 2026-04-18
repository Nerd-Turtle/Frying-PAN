from io import BytesIO
from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.session import SessionLocal
from app.models.change_set import ChangeSet
from app.models.config_object import ConfigObject
from app.models.scope import Scope
from app.models.working_object import WorkingObject
from app.models.working_reference import WorkingReference
from app.main import app
from tests.support import register_and_login


EXAMPLE_XML_PATH = Path("/opt/frying-pan/Example-1.xml")


def _client() -> TestClient:
    return TestClient(app)


def test_change_set_create_read_and_status_transition_validation() -> None:
    project_name = f"project-{uuid4()}"

    with _client() as client:
        register_and_login(client)
        project_response = client.post(
            "/api/projects",
            json={"name": project_name, "description": "Change set lifecycle test"},
        )
        project_id = project_response.json()["id"]

        create_response = client.post(
            f"/api/projects/{project_id}/change-sets",
            json={"name": "Draft set", "description": "Phase 5 draft"},
        )
        assert create_response.status_code == 200
        change_set = create_response.json()
        assert change_set["status"] == "draft"

        read_response = client.get(
            f"/api/projects/{project_id}/change-sets/{change_set['id']}"
        )
        assert read_response.status_code == 200
        assert read_response.json()["id"] == change_set["id"]

        preview_status = client.patch(
            f"/api/projects/{project_id}/change-sets/{change_set['id']}/status",
            json={"status": "preview"},
        )
        assert preview_status.status_code == 200
        assert preview_status.json()["status"] == "preview"

        applied_status = client.patch(
            f"/api/projects/{project_id}/change-sets/{change_set['id']}/status",
            json={"status": "applied"},
        )
        assert applied_status.status_code == 409
        assert applied_status.json()["detail"] == "Unsupported change set status transition."


def test_merge_preview_plans_promotions_rewrites_and_selected_normalizations() -> None:
    project_name = f"project-{uuid4()}"
    xml_bytes = EXAMPLE_XML_PATH.read_bytes()

    with _client() as client:
        register_and_login(client)
        project_response = client.post(
            "/api/projects",
            json={"name": project_name, "description": "Merge preview planning test"},
        )
        project_id = project_response.json()["id"]

        upload_response = client.post(
            f"/api/projects/{project_id}/sources/upload",
            files={"file": ("Example-1.xml", BytesIO(xml_bytes), "application/xml")},
        )
        assert upload_response.status_code == 201

        with SessionLocal() as db:
            scope_alias = Scope
            objects = db.scalars(
                select(ConfigObject)
                .join(scope_alias, ConfigObject.scope_id == scope_alias.id)
                .where(ConfigObject.project_id == project_id)
            ).all()
            object_by_key = {
                (obj.object_name, obj.object_type, obj.scope.scope_path): obj for obj in objects
            }

        dg1_group = object_by_key[
            ("DG1-Group", "address_group", "shared/device-group:Device-Group-1")
        ]
        dg1_service_group = object_by_key[
            ("DG1-Service-Group", "service_group", "shared/device-group:Device-Group-1")
        ]
        dg1_sub_dup = object_by_key[
            (
                "DUP-IP-ADDRESS",
                "address",
                "shared/device-group:Device-Group-1/device-group:DG1-Sub-Group",
            )
        ]

        preview_response = client.post(
            f"/api/projects/{project_id}/merge/preview",
            json={
                "name": "Promote DG1 objects",
                "description": "Preview promoting selected objects",
                "selected_object_ids": [dg1_group.id, dg1_service_group.id],
                "selected_normalizations": [
                    {"object_id": dg1_sub_dup.id, "kind": "host_ipv4_to_cidr"}
                ],
            },
        )
        assert preview_response.status_code == 200
        change_set = preview_response.json()

        assert change_set["status"] == "preview"
        assert change_set["preview_summary"]["planned_object_count"] == 3
        assert change_set["preview_summary"]["normalization_count"] == 1
        assert change_set["preview_summary"]["blocked_object_count"] == 0

        object_ops = change_set["operations_payload"]["object_operations"]
        promoted_names = {item["object_name"] for item in object_ops}
        assert promoted_names == {"DG1-Group", "DG1-IP-Netmask", "DG1-Service-Group"}

        rewrites = change_set["operations_payload"]["reference_rewrites"]
        rewrite_targets = {(item["owner_object_name"], item["target_name"]) for item in rewrites}
        assert ("Nested-Groups", "DG1-Group") in rewrite_targets
        assert ("DG1-Group", "DG1-IP-Netmask") in rewrite_targets

        normalization_ops = change_set["operations_payload"]["normalization_operations"]
        assert normalization_ops == [
            {
                "operation": "normalize_object_value",
                "object_id": dg1_sub_dup.id,
                "object_name": "DUP-IP-ADDRESS",
                "object_type": "address",
                "scope_path": "shared/device-group:Device-Group-1/device-group:DG1-Sub-Group",
                "kind": "host_ipv4_to_cidr",
                "from_value": "172.16.1.1",
                "to_value": "172.16.1.1/32",
            }
        ]

        with SessionLocal() as db:
            persisted_change_set = db.scalars(
                select(ChangeSet).where(ChangeSet.id == change_set["id"])
            ).one()

        assert persisted_change_set.status == "preview"


def test_merge_preview_records_blockers_for_unsafe_plans() -> None:
    project_name = f"project-{uuid4()}"
    xml_bytes = EXAMPLE_XML_PATH.read_bytes()

    with _client() as client:
        register_and_login(client)
        project_response = client.post(
            "/api/projects",
            json={"name": project_name, "description": "Unsafe preview test"},
        )
        project_id = project_response.json()["id"]

        upload_response = client.post(
            f"/api/projects/{project_id}/sources/upload",
            files={"file": ("Example-1.xml", BytesIO(xml_bytes), "application/xml")},
        )
        assert upload_response.status_code == 201

        with SessionLocal() as db:
            collision_object = db.scalars(
                select(ConfigObject)
                .join(Scope, ConfigObject.scope_id == Scope.id)
                .where(
                    ConfigObject.project_id == project_id,
                    ConfigObject.object_name == "DUP-IP-ADDRESS",
                    Scope.scope_path
                    == "shared/device-group:Device-Group-1/device-group:DG1-Sub-Group",
                )
            ).one()

        preview_response = client.post(
            f"/api/projects/{project_id}/merge/preview",
            json={
                "name": "Unsafe preview",
                "description": "Expect blocker",
                "selected_object_ids": [collision_object.id],
                "selected_normalizations": [],
            },
        )
        assert preview_response.status_code == 200
        change_set = preview_response.json()

        assert change_set["preview_summary"]["planned_object_count"] == 0
        assert change_set["preview_summary"]["blocked_object_count"] == 1
        assert change_set["operations_payload"]["object_operations"] == []

        blocked = change_set["operations_payload"]["blocked_objects"]
        assert blocked[0]["object_name"] == "DUP-IP-ADDRESS"
        assert "name_collision_in_shared" in blocked[0]["blockers"]


def test_apply_change_set_preserves_imported_state_and_updates_working_state_transactionally() -> None:
    project_name = f"project-{uuid4()}"
    xml_bytes = EXAMPLE_XML_PATH.read_bytes()

    with _client() as client:
        register_and_login(client)
        project_response = client.post(
            "/api/projects",
            json={"name": project_name, "description": "Apply engine success test"},
        )
        project_id = project_response.json()["id"]

        upload_response = client.post(
            f"/api/projects/{project_id}/sources/upload",
            files={"file": ("Example-1.xml", BytesIO(xml_bytes), "application/xml")},
        )
        assert upload_response.status_code == 201

        with SessionLocal() as db:
            objects = db.scalars(
                select(ConfigObject).join(Scope, ConfigObject.scope_id == Scope.id).where(
                    ConfigObject.project_id == project_id
                )
            ).all()
            object_by_key = {
                (obj.object_name, obj.object_type, obj.scope.scope_path): obj for obj in objects
            }

        dg1_group = object_by_key[
            ("DG1-Group", "address_group", "shared/device-group:Device-Group-1")
        ]
        dg1_service_group = object_by_key[
            ("DG1-Service-Group", "service_group", "shared/device-group:Device-Group-1")
        ]
        dg1_sub_dup = object_by_key[
            (
                "DUP-IP-ADDRESS",
                "address",
                "shared/device-group:Device-Group-1/device-group:DG1-Sub-Group",
            )
        ]

        preview_response = client.post(
            f"/api/projects/{project_id}/merge/preview",
            json={
                "name": "Applyable preview",
                "description": "Promote and normalize",
                "selected_object_ids": [dg1_group.id, dg1_service_group.id],
                "selected_normalizations": [
                    {"object_id": dg1_sub_dup.id, "kind": "host_ipv4_to_cidr"}
                ],
            },
        )
        assert preview_response.status_code == 200
        change_set = preview_response.json()

        apply_response = client.post(
            f"/api/projects/{project_id}/change-sets/{change_set['id']}/apply"
        )
        assert apply_response.status_code == 200
        applied = apply_response.json()
        assert applied["status"] == "applied"
        assert applied["applied_at"] is not None

        with SessionLocal() as db:
            source_dup = db.scalars(
                select(ConfigObject)
                .join(Scope, ConfigObject.scope_id == Scope.id)
                .where(
                    ConfigObject.project_id == project_id,
                    ConfigObject.object_name == "DUP-IP-ADDRESS",
                    Scope.scope_path
                    == "shared/device-group:Device-Group-1/device-group:DG1-Sub-Group",
                )
            ).one()

            working_objects = db.scalars(
                select(WorkingObject)
                .options(selectinload(WorkingObject.scope))
                .join(Scope, WorkingObject.scope_id == Scope.id)
                .where(WorkingObject.project_id == project_id)
            ).all()
            working_refs = db.scalars(
                select(WorkingReference).where(WorkingReference.project_id == project_id)
            ).all()

        assert source_dup.raw_payload["value"] == "172.16.1.1"
        assert source_dup.normalized_payload["address_text"] == "172.16.1.1"

        working_object_by_source = {obj.source_object_id: obj for obj in working_objects}
        promoted_group = working_object_by_source[dg1_group.id]
        promoted_service_group = working_object_by_source[dg1_service_group.id]
        normalized_dup = working_object_by_source[dg1_sub_dup.id]

        assert promoted_group.scope.scope_path == "shared"
        assert promoted_service_group.scope.scope_path == "shared"
        assert normalized_dup.raw_payload["value"] == "172.16.1.1/32"
        assert normalized_dup.normalized_payload["address_text"] == "172.16.1.1/32"

        nested_rewrite = next(
            ref
            for ref in working_refs
            if ref.target_name == "DG1-Group"
            and ref.metadata_json.get("resolved_scope_path") == "shared"
        )
        assert nested_rewrite.resolution_status == "resolved_in_shared"
        assert nested_rewrite.resolved_object_id == promoted_group.id


def test_apply_change_set_failure_rolls_back_working_state_changes() -> None:
    project_name = f"project-{uuid4()}"
    xml_bytes = EXAMPLE_XML_PATH.read_bytes()

    with _client() as client:
        register_and_login(client)
        project_response = client.post(
            "/api/projects",
            json={"name": project_name, "description": "Apply engine rollback test"},
        )
        project_id = project_response.json()["id"]

        upload_response = client.post(
            f"/api/projects/{project_id}/sources/upload",
            files={"file": ("Example-1.xml", BytesIO(xml_bytes), "application/xml")},
        )
        assert upload_response.status_code == 201

        with SessionLocal() as db:
            dg1_service_group = db.scalars(
                select(ConfigObject)
                .join(Scope, ConfigObject.scope_id == Scope.id)
                .where(
                    ConfigObject.project_id == project_id,
                    ConfigObject.object_name == "DG1-Service-Group",
                    Scope.scope_path == "shared/device-group:Device-Group-1",
                )
            ).one()

        preview_response = client.post(
            f"/api/projects/{project_id}/merge/preview",
            json={
                "name": "Tampered preview",
                "description": "Will fail on apply",
                "selected_object_ids": [dg1_service_group.id],
                "selected_normalizations": [],
            },
        )
        assert preview_response.status_code == 200
        change_set = preview_response.json()

        with SessionLocal() as db:
            persisted = db.scalars(
                select(ChangeSet).where(ChangeSet.id == change_set["id"])
            ).one()
            tampered_payload = dict(persisted.operations_payload)
            tampered_object_ops = list(tampered_payload["object_operations"])
            tampered_object_ops[0] = {
                **tampered_object_ops[0],
                "object_id": "missing-object-id",
            }
            tampered_payload["object_operations"] = tampered_object_ops
            persisted.operations_payload = tampered_payload
            db.add(persisted)
            db.commit()

        apply_response = client.post(
            f"/api/projects/{project_id}/change-sets/{change_set['id']}/apply"
        )
        assert apply_response.status_code == 409

        with SessionLocal() as db:
            working_object_count = db.scalars(
                select(WorkingObject.id).where(WorkingObject.project_id == project_id)
            ).all()
            working_reference_count = db.scalars(
                select(WorkingReference.id).where(WorkingReference.project_id == project_id)
            ).all()
            persisted = db.scalars(
                select(ChangeSet).where(ChangeSet.id == change_set["id"])
            ).one()

        assert working_object_count == []
        assert working_reference_count == []
        assert persisted.status == "preview"
        assert persisted.applied_at is None

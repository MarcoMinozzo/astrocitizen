"""AC-222 / AC-223 — sync_queue Desktop + SaaS master store."""

from __future__ import annotations

import json
from pathlib import Path

from astrocitizen.adapters.sqlite import SqliteArchive
from astrocitizen.adapters.sqlite.schema import SCHEMA_VERSION
from astrocitizen.observatory.models import ObservationRecord
from astrocitizen.saas.store import SaasMasterStore
from astrocitizen.shared.ids import new_id
from astrocitizen.sync import SyncClient, SyncEnqueueService
from astrocitizen.sync.canonical import observation_canonical
from astrocitizen.workspace.models import Workspace


def test_schema_v10_sync_queue(tmp_path: Path) -> None:
    assert SCHEMA_VERSION >= 10
    archive = SqliteArchive(tmp_path / "s.sqlite3")
    assert archive.migrate() == SCHEMA_VERSION
    names = {
        r[0]
        for r in archive._conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    }
    assert "sync_queue" in names
    assert "sync_cursor" in names
    archive.close()


def test_enqueue_observation_and_push(tmp_path: Path) -> None:
    archive = SqliteArchive(tmp_path / "d.sqlite3")
    archive.migrate()
    ws = archive.upsert_workspace(Workspace(id=new_id(), name="ws"))
    obs = archive.save_observation(
        ObservationRecord(
            id=new_id(),
            workspace_id=ws.id,
            observed_at_utc="2026-07-24T01:00:00Z",
            notes="sync-test",
        )
    )
    item = SyncEnqueueService(archive).enqueue_observation(obs.id)
    assert item.status == "pending"
    pending = archive.list_sync_queue(status="pending")
    assert len(pending) == 1
    assert pending[0].payload["notes"] == "sync-test"

    master = SaasMasterStore(tmp_path / "master.sqlite3")

    def opener(url: str, data: bytes, headers: dict) -> str:
        assert "/sync/batch" in url
        assert headers.get("Authorization", "").startswith("Bearer ")
        body = json.loads(data.decode("utf-8"))
        results = [master.apply_operation(op) for op in body["operations"]]
        return json.dumps({"results": results, "conflicts": []})

    client = SyncClient(
        archive,
        base_url="http://saas.test",
        token="dev",
        workspace_id=ws.id,
        opener=opener,
    )
    out = client.push_pending()
    assert out["pushed"] == 1
    assert out["results"][0]["status"] == "accepted"
    assert archive.list_sync_queue(status="pending") == []
    assert archive.list_sync_queue(status="acked")
    listed = master.list_observations(workspace_id=str(ws.id))
    assert len(listed) == 1
    assert listed[0]["id"] == str(obs.id)

    # Idempotência: re-aplicar mesmo client_op_id
    again = master.apply_operation(
        {
            "client_op_id": str(item.client_op_id),
            "entity": "observation",
            "payload": observation_canonical(obs),
        }
    )
    assert again.get("idempotent") is True
    master.close()
    archive.close()


def test_saas_app_health_and_batch(tmp_path: Path) -> None:
    try:
        from fastapi.testclient import TestClient
    except ImportError:
        return  # saas extra opcional

    from astrocitizen.saas.app import DEV_TOKEN, create_app

    store = SaasMasterStore(tmp_path / "api.sqlite3")
    app = create_app(store=store)
    client = TestClient(app)
    assert client.get("/health").json()["status"] == "ok"
    tok = client.post(
        "/auth/token", json={"email": "a@b.c", "password": "x"}
    ).json()["access_token"]
    assert tok == DEV_TOKEN
    oid = str(new_id())
    ws = str(new_id())
    op_id = str(new_id())
    resp = client.post(
        "/sync/batch",
        headers={"Authorization": f"Bearer {DEV_TOKEN}"},
        json={
            "device_id": "t",
            "operations": [
                {
                    "client_op_id": op_id,
                    "entity": "observation",
                    "operation": "upsert",
                    "payload": {
                        "id": oid,
                        "workspace_id": ws,
                        "observed_at_utc": "2026-07-24T02:00:00Z",
                        "notes": "via-api",
                        "version": 1,
                    },
                    "client_timestamp_utc": "2026-07-24T02:00:00Z",
                }
            ],
        },
    )
    assert resp.status_code == 200
    assert resp.json()["results"][0]["status"] == "accepted"
    got = client.get(
        "/observations",
        headers={
            "Authorization": f"Bearer {DEV_TOKEN}",
            "X-Workspace-Id": ws,
        },
    )
    assert got.status_code == 200
    assert got.json()["count"] == 1
    store.close()

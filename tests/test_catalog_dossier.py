"""AC-235 — catálogo próprio / ficha celeste + buffer."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from astrocitizen.adapters.sqlite import SqliteArchive
from astrocitizen.adapters.sqlite.schema import SCHEMA_VERSION
from astrocitizen.catalog.dossier import CatalogDossierService
from astrocitizen.catalog.models import SECTION_ORDER, dossier_from_resolved
from astrocitizen.integrations.catalog_service import CatalogResolveService
from astrocitizen.saas.store import SaasMasterStore
from astrocitizen.shared.ids import new_id
from astrocitizen.sync.service import SyncEnqueueService
from astrocitizen.workspace.models import Workspace


def _resolved_sscyg() -> dict[str, Any]:
    return {
        "designation": "SS Cyg",
        "ra_deg": 325.67833,
        "dec_deg": 43.58608,
        "sources": ["sesame", "vsx", "simbad"],
        "external_ids": {
            "otype": "CV*",
            "variability_type": "UGSS",
            "mag_max": 7.7,
            "mag_min": 12.4,
            "period": 0.275,
            "auid": "000-BCT-697",
            "simbad": "SS Cyg",
            "gmag": 11.2,
            "gaia_source_id": "123",
            "parallax_mas": 8.5,
            "pmra": 1.1,
            "pmdec": -2.2,
        },
    }


def test_schema_v11_catalog_objects(tmp_path: Path) -> None:
    assert SCHEMA_VERSION >= 11
    archive = SqliteArchive(tmp_path / "c.sqlite3")
    assert archive.migrate() == SCHEMA_VERSION
    names = {
        r[0]
        for r in archive._conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    }
    assert "catalog_objects" in names
    archive.close()


def test_dossier_sections_from_resolved() -> None:
    sections = dossier_from_resolved(
        _resolved_sscyg(), query="SS Cyg", fetched_at="2026-07-24T00:00:00Z"
    )
    assert set(sections.keys()) == set(SECTION_ORDER)
    assert sections["identity"]["designation"] == "SS Cyg"
    assert sections["position"]["ra_deg"] == 325.67833
    assert sections["photometry"]["mag_max"] == 7.7
    assert sections["variability"]["variability_type"] == "UGSS"
    assert sections["astrometry"]["parallax_mas"] == 8.5
    assert "sesame" in (sections["provenance"]["sources"] or "")


def test_dossier_upsert_on_lookup(tmp_path: Path) -> None:
    archive = SqliteArchive(tmp_path / "d.sqlite3")
    archive.migrate()
    ws = archive.upsert_workspace(Workspace(id=new_id(), name="ws"))

    class _FakeResolve(CatalogResolveService):
        def resolve(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
            return _resolved_sscyg()

    svc = CatalogDossierService(archive, resolve_service=_FakeResolve(archive))
    obj = svc.lookup(ws.id, "SS Cyg", network=True, enqueue_sync=True)
    assert obj.designation == "SS Cyg"
    assert obj.ra_deg is not None
    assert abs(obj.ra_deg - 325.67833) < 1e-5
    assert "position" in obj.sections

    again = svc.lookup(ws.id, "SS Cyg", network=True, enqueue_sync=False)
    assert again.id == obj.id
    assert again.version >= 2

    listed = svc.list(ws.id)
    assert len(listed) == 1
    assert listed[0].query_name == "SS Cyg"

    pending = archive.list_sync_queue(status="pending")
    assert any(it.entity_type == "catalog_object" for it in pending)
    archive.close()


def test_saas_accepts_catalog_object(tmp_path: Path) -> None:
    archive = SqliteArchive(tmp_path / "d.sqlite3")
    archive.migrate()
    ws = archive.upsert_workspace(Workspace(id=new_id(), name="ws"))

    class _FakeResolve(CatalogResolveService):
        def resolve(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
            return _resolved_sscyg()

    obj = CatalogDossierService(archive, resolve_service=_FakeResolve(archive)).lookup(
        ws.id, "SS Cyg", enqueue_sync=True
    )
    item = SyncEnqueueService(archive).enqueue_catalog_object(obj.id)
    master = SaasMasterStore(tmp_path / "master.sqlite3")
    ack = master.apply_operation(
        {
            "client_op_id": str(item.client_op_id),
            "entity": "catalog_object",
            "operation": "upsert",
            "payload": item.payload,
        }
    )
    assert ack["status"] == "accepted"
    row = master._conn.execute(
        "SELECT designation FROM catalog_objects WHERE id = ?",
        (str(obj.id),),
    ).fetchone()
    assert row is not None
    assert row["designation"] == "SS Cyg"
    master.close()
    archive.close()


def test_catalog_panel_factory() -> None:
    from astrocitizen.desktop.catalog_panel import build_catalog_dashboard

    assert callable(build_catalog_dashboard)

"""D-013 / E21: form schemas + institutional cache."""

from __future__ import annotations

import json
from pathlib import Path

from astrocitizen.adapters.sqlite import SqliteArchive
from astrocitizen.adapters.sqlite.schema import SCHEMA_VERSION
from astrocitizen.integrations.form_schemas import list_form_networks, load_form_schema
from astrocitizen.integrations.vsx import VsxProvider


def test_schema_version_includes_cache() -> None:
    assert SCHEMA_VERSION >= 9


def test_load_aavso_form_schema() -> None:
    schema = load_form_schema("aavso")
    assert schema["network"] == "aavso"
    ids = {f["id"] for f in schema["fields"]}
    assert {"star", "obscode", "band", "chart", "product_id"} <= ids
    assert "aavso" in list_form_networks()


def test_institutional_cache_roundtrip(tmp_path: Path) -> None:
    archive = SqliteArchive(tmp_path / "c.sqlite3")
    assert archive.migrate() == SCHEMA_VERSION
    archive.upsert_institutional_cache(
        provider="vsx",
        object_id="SS Cyg",
        payload={"ra_deg": 1.0, "designation": "SS Cyg"},
    )
    row = archive.get_institutional_cache(provider="vsx", object_id="SS Cyg")
    assert row is not None
    assert row["payload"]["ra_deg"] == 1.0
    listed = archive.list_institutional_cache(provider="vsx")
    assert len(listed) == 1
    archive.close()


def test_vsx_provider_writes_cache(tmp_path: Path) -> None:
    sample = {
        "VSXObject": {
            "Name": "SS Cyg",
            "AUID": "000-BCP-220",
            "RA2000": "325.67833",
            "Declination2000": "43.58608",
            "VariabilityType": "UGSS",
            "OID": "1",
        }
    }

    class Fake:
        def resolve(self, name: str) -> dict:
            from astrocitizen.adapters.sky.vsx_resolver import VsxResolver

            return VsxResolver(opener=lambda _u: json.dumps(sample)).resolve(name)

    archive = SqliteArchive(tmp_path / "v.sqlite3")
    archive.migrate()
    p = VsxProvider(resolver=Fake(), archive=archive)
    out = p.search_object("SS Cyg")
    assert out["external_ids"]["auid"] == "000-BCP-220"
    by_auid = archive.get_institutional_cache(
        provider="vsx", object_id="000-BCP-220"
    )
    assert by_auid is not None
    by_name = archive.get_institutional_cache(provider="vsx", object_id="SS Cyg")
    assert by_name is not None
    archive.close()

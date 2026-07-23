"""AC-096: VSX resolver, AEF rigoroso, WebObs oficial."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from astrocitizen.adapters.aavso_portal import WEBOBS_URL
from astrocitizen.adapters.sky.vsx_resolver import VsxResolver
from astrocitizen.adapters.sqlite import SqliteArchive
from astrocitizen.contribution.aavso import format_aavso_extended
from astrocitizen.contribution.validate_minimum import validate_product_for_network
from astrocitizen.desktop.contribute import _star_from_product, prefill_aavso_fields
from astrocitizen.planning.models import Target
from astrocitizen.reduction.models import AnalysisProduct
from astrocitizen.shared.errors import DomainError, NotFoundError
from astrocitizen.shared.ids import new_id
from astrocitizen.workspace.models import Workspace


def test_webobs_url_constant() -> None:
    assert WEBOBS_URL.startswith("https://")
    assert "webobs" in WEBOBS_URL.lower()


def test_vsx_resolver_parses_object() -> None:
    sample = {
        "VSXObject": {
            "Name": "SS Cyg",
            "AUID": "000-BCP-220",
            "RA2000": "325.67833",
            "Declination2000": "43.58608",
            "VariabilityType": "UGSS",
            "Period": "0.2751300",
            "MaxMag": "7.7 V",
            "MinMag": "12.4 V",
            "OID": "10939",
        }
    }

    def opener(_url: str) -> str:
        return json.dumps(sample)

    resolved = VsxResolver(opener=opener).resolve("SS Cyg")
    assert abs(resolved["ra_deg"] - 325.67833) < 1e-5
    assert abs(resolved["dec_deg"] - 43.58608) < 1e-5
    assert resolved["external_ids"]["auid"] == "000-BCP-220"
    assert resolved["external_ids"]["variability_type"] == "UGSS"
    assert resolved["external_ids"]["period"] == pytest.approx(0.27513)
    assert resolved["designation"] == "SS Cyg"


def test_vsx_resolver_not_found() -> None:
    def opener(_url: str) -> str:
        return json.dumps({})

    with pytest.raises(NotFoundError):
        VsxResolver(opener=opener).resolve("NO SUCH STAR")


def test_format_aef_rejects_unusable_points() -> None:
    with pytest.raises(DomainError, match="nenhum ponto"):
        format_aavso_extended(
            star_name="SS CYG",
            observer_code="XYZ",
            points=[{"t_utc": "not-a-date", "y": 12.0}],
        )


def test_validate_aavso_rejects_bad_jd(tmp_path: Path) -> None:
    archive = SqliteArchive(tmp_path / "v.sqlite3")
    archive.migrate()
    ws = archive.upsert_workspace(Workspace(id=new_id(), name="ws"))
    product = archive.save_analysis_product(
        AnalysisProduct(
            id=new_id(),
            workspace_id=ws.id,
            product_type="light_curve",
            version_num=1,
            is_publishable=False,
            parameters={},
            summary={},
            state="ready",
        )
    )
    archive.save_measurement_points(
        product.id,
        [{"t_utc": "bad", "sequence_index": 0, "x": 0.0, "y": 12.1, "band": "V"}],
    )
    bad = validate_product_for_network(
        archive,
        network="aavso",
        product_id=product.id,
        payload={"obscode": "XYZ", "star": "SS CYG", "chart": "X123"},
    )
    assert not bad.ok
    assert any(i.code == "aavso_jd" for i in bad.issues)
    archive.close()


def test_validate_aavso_warns_chart_na(tmp_path: Path) -> None:
    archive = SqliteArchive(tmp_path / "v2.sqlite3")
    archive.migrate()
    ws = archive.upsert_workspace(Workspace(id=new_id(), name="ws"))
    product = archive.save_analysis_product(
        AnalysisProduct(
            id=new_id(),
            workspace_id=ws.id,
            product_type="light_curve",
            version_num=1,
            is_publishable=False,
            parameters={},
            summary={},
            state="ready",
        )
    )
    archive.save_measurement_points(
        product.id,
        [
            {
                "t_utc": "2026-07-23T01:00:00Z",
                "sequence_index": 0,
                "x": 0.0,
                "y": 12.1,
                "y_err": 0.02,
                "band": "V",
            }
        ],
    )
    r = validate_product_for_network(
        archive,
        network="aavso",
        product_id=product.id,
        payload={"obscode": "XYZ", "star": "SS CYG", "chart": "NA"},
    )
    assert r.ok
    assert any(i.code == "aavso_chart" and i.severity == "warning" for i in r.issues)
    archive.close()


def test_prefill_prefers_auid(tmp_path: Path) -> None:
    archive = SqliteArchive(tmp_path / "p.sqlite3")
    archive.migrate()
    ws = archive.upsert_workspace(Workspace(id=new_id(), name="ws"))
    tid = new_id()
    archive.upsert_target(
        Target(
            id=tid,
            workspace_id=ws.id,
            designation="SS Cyg",
            ra_deg=325.67,
            dec_deg=43.58,
            target_type="variable",
            external_ids={"auid": "000-BCP-220", "vsx": "SS Cyg"},
        )
    )
    product = archive.save_analysis_product(
        AnalysisProduct(
            id=new_id(),
            workspace_id=ws.id,
            product_type="light_curve",
            version_num=1,
            is_publishable=False,
            parameters={"target_id": str(tid)},
            summary={},
            state="ready",
        )
    )
    assert _star_from_product(archive, product) == "000-BCP-220"
    fields = prefill_aavso_fields(
        archive,
        credentials={"obscode": "ABC"},
        current={"product_id": str(product.id)},
    )
    assert fields["star"] == "000-BCP-220"
    archive.close()

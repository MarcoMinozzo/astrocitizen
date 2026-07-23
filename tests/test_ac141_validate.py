"""AC-141 product-minimum validation + D-011 image tool helpers."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

from astrocitizen.adapters.image_tools import build_command
from astrocitizen.adapters.sqlite import SqliteArchive
from astrocitizen.contribution.validate_minimum import validate_product_for_network
from astrocitizen.reduction.models import AnalysisProduct
from astrocitizen.shared.ids import new_id
from astrocitizen.workspace.models import Workspace


def test_build_command_substitutes_path(tmp_path: Path) -> None:
    f = tmp_path / "a.fits"
    f.write_bytes(b"x")
    argv = build_command("ds9 %f", f)
    assert argv == ["ds9", str(f)]


def test_validate_aavso_requires_points(tmp_path: Path) -> None:
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
    bad = validate_product_for_network(
        archive,
        network="aavso",
        product_id=product.id,
        payload={"obscode": "XYZ", "star": "SS CYG"},
    )
    assert not bad.ok
    assert any(i.code == "aavso_points" for i in bad.issues)

    archive.save_measurement_points(
        product.id,
        [
            {
                "t_utc": "2026-07-23T01:00:00Z",
                "sequence_index": 0,
                "x": 0.0,
                "y": 12.1,
                "band": "V",
            }
        ],
    )
    ok = validate_product_for_network(
        archive,
        network="aavso",
        product_id=product.id,
        payload={"obscode": "XYZ", "star": "SS CYG"},
    )
    assert ok.ok
    archive.close()


def test_validate_mpc_form() -> None:
    archive = SimpleNamespace(get_analysis_product=lambda _id: None)
    r = validate_product_for_network(
        archive,
        network="mpc",
        payload={
            "observatory_code": "XXX",
            "designation": "2026 AA",
            "ra_deg": 10.0,
            "dec_deg": -5.0,
            "epoch_utc": "2026-07-23T00:00:00Z",
        },
    )
    assert r.ok


def test_validate_wds_double() -> None:
    product = SimpleNamespace(
        product_type="double_measure",
        summary={"pa_deg": 10.0, "sep_arcsec": 2.0, "epoch_utc": "2026-07-23T00:00:00Z"},
        parameters={},
    )
    archive = SimpleNamespace(
        get_analysis_product=lambda _id: product,
        list_measurement_points=lambda _id: [],
    )
    r = validate_product_for_network(
        archive, network="wds", product_id=uuid4()
    )
    assert r.ok

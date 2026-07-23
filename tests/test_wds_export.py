"""Export WDS / EXP-WDS (PO-G01)."""

from __future__ import annotations

from pathlib import Path

from astrocitizen.adapters.fs import LocalArtifactStore
from astrocitizen.adapters.sqlite import SqliteArchive
from astrocitizen.contribution.validate_minimum import validate_product_for_network
from astrocitizen.contribution.wds import ExportWds, format_wds_measure
from astrocitizen.desktop.contribute import prefill_wds_fields
from astrocitizen.inventory.models import Site
from astrocitizen.observatory.double_log import LogDoubleMeasure
from astrocitizen.shared.ids import new_id
from astrocitizen.workspace.models import Workspace


def test_format_wds_measure() -> None:
    text = format_wds_measure(
        object_name="WDS 04184+2135",
        epoch_utc="2026-07-23T02:15:00Z",
        pa_deg=127.3,
        sep_arcsec=2.45,
        mag_primary=2.0,
        mag_secondary=2.9,
        method="micrometer",
        observer="Tester",
        observatory="Casa",
    )
    assert "#TYPE=ASTROCITIZEN_WDS" in text
    assert "#PA_DEG=127.300" in text
    assert "#SEP_ARCSEC=2.450" in text
    assert "WDS 04184+2135,2026-07-23T02:15:00Z,127.300,2.450,2.00,2.90" in text


def test_export_wds_from_double_product(tmp_path: Path) -> None:
    archive = SqliteArchive(tmp_path / "w.sqlite3")
    archive.migrate()
    ws = archive.upsert_workspace(Workspace(id=new_id(), name="ws"))
    site = archive.upsert_site(
        Site(
            id=new_id(),
            workspace_id=ws.id,
            name="Casa",
            latitude_deg=-29.0,
            longitude_deg=-51.0,
        )
    )
    store = LocalArtifactStore(tmp_path / "art")
    product = LogDoubleMeasure(archive, store).execute(
        workspace_id=ws.id,
        object_name="WDS 04184+2135",
        pa_deg=127.3,
        sep_arcsec=2.45,
        epoch_utc="2026-07-23T02:15:00Z",
        method="micrometer",
        mag_primary=2.0,
        mag_secondary=2.9,
        site_id=site.id,
    )
    check = validate_product_for_network(
        archive, network="wds", product_id=product.id
    )
    assert check.ok
    out = tmp_path / "measure.txt"
    ExportWds(archive).execute(product_id=product.id, out_path=out)
    text = out.read_text(encoding="utf-8")
    assert "#WDS=WDS 04184+2135" in text
    assert "#OBSERVATORY=Casa" in text
    assert out.with_suffix(".csv").is_file()
    filled = prefill_wds_fields(
        archive, current={"product_id": str(product.id)}
    )
    assert filled["object"] == "WDS 04184+2135"
    assert filled["pa_deg"] == 127.3
    assert filled["sep_arcsec"] == 2.45
    assert filled["observatory"] == "Casa"
    archive.close()

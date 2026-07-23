"""Export COBS / EXP-COBS-ICQ (PO-A10)."""

from __future__ import annotations

from pathlib import Path

from astrocitizen.adapters.sqlite import SqliteArchive
from astrocitizen.contribution.cobs import (
    ExportCobs,
    format_cobs_measure,
    utc_to_icq_date,
)
from astrocitizen.contribution.validate_minimum import validate_product_for_network
from astrocitizen.desktop.contribute import prefill_cobs_fields
from astrocitizen.inventory.models import Site
from astrocitizen.observatory.visual_log import LogVisualObservation
from astrocitizen.shared.ids import new_id
from astrocitizen.workspace.models import Workspace


def test_utc_to_icq_date() -> None:
    assert utc_to_icq_date("2026-07-23T12:00:00Z") == "2026 07 23.50"


def test_format_cobs_measure() -> None:
    text = format_cobs_measure(
        designation="C/2023 A3",
        epoch_utc="2026-07-23T06:00:00Z",
        mag=8.5,
        mag_method="B",
        aperture_cm=20.0,
        obscode="XYZ00",
        observer="Tester",
        location="Casa",
    )
    assert "#TYPE=ASTROCITIZEN_COBS" in text
    assert "#DESIGNATION=C/2023 A3" in text
    assert "#UT_DATE=2026 07 23.25" in text
    assert "#MAG=8.5" in text
    assert "submit=https://www.cobs.si/" in text.lower() or "cobs.si" in text


def test_export_cobs_from_visual_log(tmp_path: Path) -> None:
    archive = SqliteArchive(tmp_path / "c.sqlite3")
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
    product = LogVisualObservation(archive).execute(
        workspace_id=ws.id,
        object_name="C/2023 A3",
        description="coma bright",
        observed_at_utc="2026-07-23T06:00:00Z",
        magnitude=8.5,
        site_id=site.id,
        observer="CometObs",
    )
    check = validate_product_for_network(
        archive,
        network="cobs",
        product_id=product.id,
        payload={"mag_method": "B", "obscode": "XYZ00"},
    )
    assert check.ok
    out = tmp_path / "cobs.txt"
    ExportCobs(archive).execute(
        product_id=product.id,
        out_path=out,
        overrides={"mag_method": "B", "obscode": "XYZ00"},
    )
    text = out.read_text(encoding="utf-8")
    assert "#DESIGNATION=C/2023 A3" in text
    assert "#LOCATION=Casa" in text
    assert out.with_suffix(".csv").is_file()
    filled = prefill_cobs_fields(
        archive,
        credentials={"obscode": "XYZ00"},
        current={"product_id": str(product.id)},
    )
    assert filled["designation"] == "C/2023 A3"
    assert filled["mag"] == 8.5
    assert filled["location"] == "Casa"
    archive.close()


def test_validate_cobs_requires_core_fields() -> None:
    class Archive:
        def get_analysis_product(self, _id):
            return None

        def list_measurement_points(self, _id):
            return []

    bad = validate_product_for_network(
        Archive(), network="cobs", payload={"designation": "", "mag": None}
    )
    assert not bad.ok
    codes = {i.code for i in bad.issues if i.severity == "error"}
    assert "cobs_desig" in codes
    assert "cobs_mag" in codes
    assert "cobs_epoch" in codes

"""Fase 1 / AC-211 / AC-226 — Sesame + CatalogResolveService + plano com cache."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from astrocitizen.adapters.sky.sesame_resolver import SesameResolver, parse_sesame_xml
from astrocitizen.adapters.sqlite import SqliteArchive
from astrocitizen.adapters.sqlite.schema import SCHEMA_VERSION
from astrocitizen.integrations.catalog_service import (
    CatalogResolveService,
    catalog_notes_from_ids,
)
from astrocitizen.integrations.registry import ProviderRegistry
from astrocitizen.integrations.sesame import SesameProvider
from astrocitizen.integrations.simbad import SimbadProvider
from astrocitizen.inventory.models import Equipment, InstrumentConfig, Site
from astrocitizen.planning import GenerateDailyPlan, Target
from astrocitizen.programs.models import Program
from astrocitizen.programs.seed import seed_program_templates
from astrocitizen.shared.errors import NotFoundError
from astrocitizen.shared.ids import new_id
from astrocitizen.workspace.models import Workspace

_SESAME_XML = """<?xml version="1.0" encoding="UTF-8"?>
<Sesame name="SS Cyg">
  <Target name="SS Cyg">
    <Resolver name="S=Simbad">
      <otype>CV*</otype>
      <jpos>21 42 42.80 +43 35 09.9</jpos>
      <jradeg>325.67833</jradeg>
      <jdedeg>43.58608</jdedeg>
    </Resolver>
  </Target>
</Sesame>
"""


class _FakeEph:
    def night_window(self, **kwargs: Any) -> dict[str, str]:
        return {
            "start_utc": "2026-07-16T00:00:00Z",
            "end_utc": "2026-07-16T10:00:00Z",
        }

    def altitude_azimuth(self, **kwargs: Any) -> dict[str, float]:
        return {"alt_deg": 45.0, "az_deg": 180.0, "airmass": 1.4}


class _FakeMeteo:
    def forecast(self, **kwargs: Any) -> dict[str, Any]:
        return {
            "source": "manual",
            "cloud_cover_pct": 5,
            "wind_ms": 2,
            "humidity_pct": 40,
            "precipitation": False,
        }


def _setup(tmp_path: Path) -> tuple[SqliteArchive, Workspace, Site]:
    archive = SqliteArchive(tmp_path / "f1.sqlite3")
    assert archive.migrate() == SCHEMA_VERSION
    ws = archive.upsert_workspace(Workspace(id=new_id(), name="ws"))
    seed_program_templates(archive)
    site = archive.upsert_site(
        Site(
            id=new_id(),
            workspace_id=ws.id,
            name="TestSite",
            latitude_deg=-29.68,
            longitude_deg=-51.13,
            elevation_m=30.0,
            min_altitude_deg=15.0,
            is_default=True,
            meteo_thresholds={
                "max_cloud_cover_pct": 50,
                "max_wind_ms": 12,
                "max_humidity_pct": 90,
                "no_precipitation": True,
            },
        )
    )
    return archive, ws, site


def test_parse_sesame_xml() -> None:
    out = parse_sesame_xml(_SESAME_XML, query="SS Cyg")
    assert abs(out["ra_deg"] - 325.67833) < 1e-5
    assert abs(out["dec_deg"] - 43.58608) < 1e-5
    assert out["external_ids"]["otype"] == "CV*"


def test_sesame_resolver_opener() -> None:
    r = SesameResolver(opener=lambda _u: _SESAME_XML)
    out = r.resolve("SS Cyg")
    assert out["ra_deg"] > 300


def test_sesame_provider_writes_cache(tmp_path: Path) -> None:
    archive = SqliteArchive(tmp_path / "s.sqlite3")
    archive.migrate()
    p = SesameProvider(
        resolver=SesameResolver(opener=lambda _u: _SESAME_XML),
        archive=archive,
    )
    out = p.search_object("SS Cyg")
    assert out["ra_deg"] is not None
    row = archive.get_institutional_cache(provider="sesame", object_id="SS Cyg")
    assert row is not None
    archive.close()


def test_simbad_provider_writes_cache(tmp_path: Path) -> None:
    class Fake:
        def resolve(self, name: str) -> dict[str, Any]:
            return {
                "ra_deg": 10.0,
                "dec_deg": 20.0,
                "external_ids": {"simbad": name},
            }

    archive = SqliteArchive(tmp_path / "sim.sqlite3")
    archive.migrate()
    p = SimbadProvider(resolver=Fake(), archive=archive)
    p.search_object("Vega")
    row = archive.get_institutional_cache(provider="simbad", object_id="Vega")
    assert row is not None
    assert row["payload"]["ra_deg"] == 10.0
    archive.close()


def test_catalog_resolve_merge_and_cache(tmp_path: Path) -> None:
    archive = SqliteArchive(tmp_path / "c.sqlite3")
    archive.migrate()

    class FakeSesame:
        name = "sesame"
        features = frozenset({"search"})

        def supports(self, f: str) -> bool:
            return f in self.features

        def search_object(self, name: str) -> dict[str, Any]:
            return {
                "ra_deg": 325.0,
                "dec_deg": 43.0,
                "designation": name,
                "external_ids": {"sesame": name, "otype": "CV*"},
            }

    class FakeVsx:
        name = "vsx"
        features = frozenset({"search"})

        def supports(self, f: str) -> bool:
            return f in self.features

        def search_object(self, name: str) -> dict[str, Any]:
            return {
                "ra_deg": 325.1,
                "dec_deg": 43.1,
                "designation": name,
                "external_ids": {
                    "vsx": name,
                    "auid": "000-BCP-220",
                    "variability_type": "UGSS",
                    "mag_max": 7.7,
                    "period": 0.275,
                },
            }

    class FakeSimbad:
        name = "simbad"
        features = frozenset({"search"})

        def supports(self, f: str) -> bool:
            return f in self.features

        def search_object(self, name: str) -> dict[str, Any]:
            raise NotFoundError(name)

    reg = ProviderRegistry([FakeSesame(), FakeVsx(), FakeSimbad()])
    svc = CatalogResolveService(archive, registry=reg)
    out = svc.resolve("SS Cyg", providers=("sesame", "vsx", "simbad"))
    assert out["ra_deg"] == 325.0  # sesame first coords win
    assert out["external_ids"]["auid"] == "000-BCP-220"
    assert out["external_ids"]["mag_max"] == 7.7
    assert "sesame" in out["sources"] and "vsx" in out["sources"]
    assert archive.get_institutional_cache(provider="vsx", object_id="SS Cyg")
    archive.close()


def test_enrich_target_cache_only_and_plan_notes(tmp_path: Path) -> None:
    archive, ws, site = _setup(tmp_path)
    cam = archive.upsert_equipment(
        Equipment(id=new_id(), workspace_id=ws.id, type="camera", name="Cam", backend="sim")
    )
    mount = archive.upsert_equipment(
        Equipment(id=new_id(), workspace_id=ws.id, type="mount", name="Mount", backend="sim")
    )
    cfg = archive.upsert_instrument_config(
        InstrumentConfig(
            id=new_id(),
            workspace_id=ws.id,
            name="Setup",
            items={"camera": cam.id, "mount": mount.id},
        )
    )
    prog = archive.upsert_program(
        Program(
            id=new_id(),
            workspace_id=ws.id,
            template_id="PO-A01",
            name="Vars",
            state="active",
            priority=1,
            default_instrument_config_id=cfg.id,
        )
    )

    bright = archive.upsert_target(
        Target(
            id=new_id(),
            workspace_id=ws.id,
            designation="BrightStar",
            ra_deg=180.0,
            dec_deg=-30.0,
        )
    )
    faint = archive.upsert_target(
        Target(
            id=new_id(),
            workspace_id=ws.id,
            designation="FaintStar",
            ra_deg=185.0,
            dec_deg=-32.0,
        )
    )
    # Link faint first so tie-break must reorder by mag
    archive.link_program_target(prog.id, faint.id, sort_order=0)
    archive.link_program_target(prog.id, bright.id, sort_order=1)

    archive.upsert_institutional_cache(
        provider="vsx",
        object_id="BrightStar",
        payload={
            "ra_deg": 180.0,
            "dec_deg": -30.0,
            "designation": "BrightStar",
            "external_ids": {
                "vsx": "BrightStar",
                "variability_type": "UGSS",
                "mag_max": 8.0,
                "period": 0.3,
            },
        },
    )
    archive.upsert_institutional_cache(
        provider="vsx",
        object_id="FaintStar",
        payload={
            "ra_deg": 185.0,
            "dec_deg": -32.0,
            "designation": "FaintStar",
            "external_ids": {
                "vsx": "FaintStar",
                "variability_type": "RRAB",
                "mag_max": 12.5,
            },
        },
    )

    plan = GenerateDailyPlan(archive, _FakeEph(), _FakeMeteo()).execute(
        workspace_id=ws.id,
        site_id=site.id,
        night_date="2026-07-15",
    )
    blocks = archive.list_observation_blocks(plan.id)
    assert len(blocks) == 2
    # Brighter (mag 8) before fainter (mag 12.5) at same priority
    assert blocks[0].target_id == bright.id
    assert blocks[1].target_id == faint.id
    assert "mag_max=8.0" in blocks[0].notes or "mag_max=8" in blocks[0].notes
    assert "vsx_type=UGSS" in blocks[0].notes
    assert "period=" in blocks[0].notes

    # Offline: enrich without network still updates target
    svc = CatalogResolveService(archive)
    t = archive.get_target(bright.id)
    assert t is not None
    enriched = svc.enrich_target(t, network=False)
    assert enriched.external_ids.get("variability_type") == "UGSS"
    notes = catalog_notes_from_ids(enriched.external_ids)
    assert "vsx_type=UGSS" in notes
    archive.close()


def test_registry_includes_sesame() -> None:
    names = ProviderRegistry().list_names()
    assert "sesame" in names
    assert "simbad" in names
    assert "vsx" in names

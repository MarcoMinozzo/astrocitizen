"""AC-236 — SIMBAD TAP fotometria."""

from __future__ import annotations

from pathlib import Path

from astrocitizen.adapters.sky.simbad_tap import (
    SimbadTapResolver,
    _maybe_space_catalog,
    row_to_payload,
)
from astrocitizen.adapters.sqlite import SqliteArchive
from astrocitizen.integrations.catalog_service import CatalogResolveService
from astrocitizen.shared.ids import new_id
from astrocitizen.workspace.models import Workspace


_NGC1200_CSV = """main_id,otype_txt,ra,dec,U,B,V,R,I,G
"NGC  1200","EmG",45.977,-11.991,,13.0,,11.42,,
"""


def test_maybe_space_catalog() -> None:
    assert _maybe_space_catalog("NGC1200") == "NGC 1200"
    assert _maybe_space_catalog("M56") == "M 56"


def test_row_to_payload_ngc1200_photometry() -> None:
    row = {
        "main_id": "NGC  1200",
        "otype_txt": "EmG",
        "ra": "45.977",
        "dec": "-11.991",
        "B": "13.0",
        "R": "11.42",
        "V": "",
    }
    out = row_to_payload(row, query="NGC1200")
    assert out["external_ids"]["bmag"] == 13.0
    assert out["external_ids"]["rmag"] == 11.42
    assert "vmag" not in out["external_ids"]
    assert abs(float(out["external_ids"]["mag_max"]) - 11.42) < 1e-6  # ref R
    assert "SIMBAD" in (out["external_ids"].get("band_notes") or "")


def test_simbad_tap_resolver_opener() -> None:
    r = SimbadTapResolver(opener=lambda _u, _b: _NGC1200_CSV)
    out = r.resolve("NGC1200")
    assert out["external_ids"]["bmag"] == 13.0
    assert out["external_ids"]["otype"] == "EmG"


def test_catalog_resolve_merges_simbad_flux(tmp_path: Path) -> None:
    archive = SqliteArchive(tmp_path / "s.sqlite3")
    archive.migrate()
    archive.upsert_workspace(Workspace(id=new_id(), name="ws"))

    class FakeSesame:
        name = "sesame"
        features = frozenset({"search"})

        def supports(self, f: str) -> bool:
            return f in self.features

        def search_object(self, name: str) -> dict:
            return {
                "ra_deg": 45.977,
                "dec_deg": -11.991,
                "designation": name,
                "external_ids": {"sesame": name, "otype": "EmG"},
            }

    from astrocitizen.integrations.registry import ProviderRegistry

    class FakeVsx:
        name = "vsx"
        features = frozenset({"search"})

        def supports(self, f: str) -> bool:
            return f in self.features

        def search_object(self, name: str) -> dict:
            from astrocitizen.shared.errors import NotFoundError

            raise NotFoundError(name)

    class FakeSimbad:
        name = "simbad"
        features = frozenset({"search"})

        def supports(self, f: str) -> bool:
            return f in self.features

        def search_object(self, name: str) -> dict:
            from astrocitizen.shared.errors import NotFoundError

            raise NotFoundError(name)

    svc = CatalogResolveService(
        archive,
        registry=ProviderRegistry([FakeSesame(), FakeVsx(), FakeSimbad()]),
    )

    # Patch enrich to use opener CSV
    import astrocitizen.integrations.catalog_service as mod

    real = mod.CatalogResolveService._enrich_simbad_photometry

    def _fake(self, merged, *, query):  # noqa: ANN001
        from astrocitizen.adapters.sky.simbad_tap import SimbadTapResolver
        from astrocitizen.integrations.catalog_service import _merge_payload

        payload = SimbadTapResolver(opener=lambda _u, _b: _NGC1200_CSV).resolve(query)
        return _merge_payload(merged, payload, "simbad")

    mod.CatalogResolveService._enrich_simbad_photometry = _fake  # type: ignore[method-assign]
    try:
        out = svc.resolve("NGC1200", providers=("sesame", "vsx", "simbad"), network=True)
    finally:
        mod.CatalogResolveService._enrich_simbad_photometry = real  # type: ignore[method-assign]

    assert out["external_ids"]["bmag"] == 13.0
    assert out["external_ids"]["rmag"] == 11.42
    assert "simbad" in out["sources"]
    archive.close()

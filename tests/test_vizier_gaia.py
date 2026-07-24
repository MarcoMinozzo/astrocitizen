"""AC-212 / AC-213 — VizieR ASU + Gaia TAP (mock)."""

from __future__ import annotations

from pathlib import Path

from astrocitizen.adapters.sky.gaia_resolver import GaiaResolver, _parse_csv
from astrocitizen.adapters.sky.vizier_resolver import VizierResolver, _parse_asu_tsv
from astrocitizen.adapters.sqlite import SqliteArchive
from astrocitizen.integrations.catalog_service import CatalogResolveService
from astrocitizen.integrations.gaia import GaiaProvider
from astrocitizen.integrations.registry import ProviderRegistry
from astrocitizen.integrations.vizier import VizierProvider
from astrocitizen.shared.errors import NotFoundError

_VIZIER_TSV = """\
# VizieR ASU mock
RA_ICRS\tDE_ICRS\tSource\tGmag\t_r
325.67833\t43.58608\t1932569716049304448\t12.1\t0.001
"""

_GAIA_CSV = """\
source_id,ra,dec,phot_g_mean_mag,parallax,pmra,pmdec,dist
1932569716049304448,325.67833,43.58608,12.05,0.5,1.0,-2.0,0.0001
"""


def test_parse_vizier_tsv() -> None:
    rows = _parse_asu_tsv(_VIZIER_TSV)
    assert len(rows) == 1
    assert rows[0]["Source"].startswith("1932")


def test_vizier_resolver_and_cache(tmp_path: Path) -> None:
    archive = SqliteArchive(tmp_path / "v.sqlite3")
    archive.migrate()
    p = VizierProvider(
        resolver=VizierResolver(opener=lambda _u: _VIZIER_TSV),
        archive=archive,
    )
    out = p.search_object("SS Cyg")
    assert abs(out["ra_deg"] - 325.67833) < 1e-4
    assert out["external_ids"]["gmag"] == 12.1
    assert archive.get_institutional_cache(provider="vizier", object_id="SS Cyg")
    archive.close()


def test_parse_gaia_csv() -> None:
    rows = _parse_csv(_GAIA_CSV)
    assert rows[0]["source_id"] == "1932569716049304448"


def test_gaia_resolve_near_and_cache(tmp_path: Path) -> None:
    archive = SqliteArchive(tmp_path / "g.sqlite3")
    archive.migrate()

    def opener(_url: str, _body: bytes | None = None) -> str:
        return _GAIA_CSV

    p = GaiaProvider(resolver=GaiaResolver(opener=opener), archive=archive)
    out = p.search_near(325.67833, 43.58608)
    assert out["external_ids"]["gaia_source_id"] == "1932569716049304448"
    assert out["external_ids"]["gmag"] == 12.05
    archive.close()


def test_gaia_search_object_rejects_name() -> None:
    p = GaiaProvider(resolver=GaiaResolver(opener=lambda *_a, **_k: _GAIA_CSV))
    try:
        p.search_object("SS Cyg")
        raise AssertionError("expected NotFoundError")
    except NotFoundError:
        pass


def test_catalog_resolve_cone_enrich(tmp_path: Path) -> None:
    archive = SqliteArchive(tmp_path / "c.sqlite3")
    archive.migrate()

    class FakeSesame:
        name = "sesame"
        features = frozenset({"search"})

        def supports(self, f: str) -> bool:
            return f in self.features

        def search_object(self, name: str) -> dict:
            return {
                "ra_deg": 325.0,
                "dec_deg": 43.0,
                "designation": name,
                "external_ids": {"sesame": name},
            }

    class FakeVizier:
        name = "vizier"
        features = frozenset({"search"})

        def supports(self, f: str) -> bool:
            return f in self.features

        def search_object(self, name: str) -> dict:
            raise NotFoundError(name)

        def search_near(self, ra: float, dec: float, **kwargs) -> dict:
            return {
                "ra_deg": ra,
                "dec_deg": dec,
                "designation": "viz",
                "external_ids": {
                    "vizier": "I/355/gaiadr3",
                    "gmag": 11.2,
                    "gaia_source_id": "1",
                },
            }

    class FakeGaia:
        name = "gaia"
        features = frozenset({"search"})

        def supports(self, f: str) -> bool:
            return f in self.features

        def search_object(self, name: str) -> dict:
            raise NotFoundError(name)

        def search_near(self, ra: float, dec: float, **kwargs) -> dict:
            return {
                "ra_deg": ra,
                "dec_deg": dec,
                "designation": "2",
                "external_ids": {
                    "gaia_source_id": "2",
                    "gmag": 11.0,
                    "parallax_mas": 1.2,
                },
            }

    svc = CatalogResolveService(
        archive,
        registry=ProviderRegistry([FakeSesame(), FakeVizier(), FakeGaia()]),
    )
    out = svc.resolve("SS Cyg", providers=("sesame", "vizier", "gaia"))
    assert "sesame" in out["sources"]
    assert "vizier" in out["sources"]
    assert "gaia" in out["sources"]
    assert out["external_ids"]["gaia_source_id"] == "2"
    assert out["external_ids"]["parallax_mas"] == 1.2
    # G de estrela no cone nao vira mag_max do alvo
    assert out["external_ids"].get("mag_max") is None
    assert out["external_ids"]["gmag"] == 11.0
    assert out["designation"] == "SS Cyg"  # nao source_id Gaia
    archive.close()


def test_extended_object_skips_stellar_cone_and_keeps_name() -> None:
    from astrocitizen.integrations.catalog_service import _merge_payload, _is_extended_object

    assert _is_extended_object({"otype": "GlC"})
    base = {
        "query": "M56",
        "designation": "M56",
        "ra_deg": 289.1,
        "dec_deg": 30.1,
        "external_ids": {"otype": "GlC", "sesame": "M56"},
        "sources": ["sesame"],
    }
    gaia = {
        "designation": "2039254015507205888",
        "ra_deg": 289.1,
        "dec_deg": 30.1,
        "external_ids": {"gmag": 17.7, "gaia_source_id": "2039254015507205888", "mag_max": 17.7},
    }
    out = _merge_payload(base, gaia, "gaia")
    assert out["designation"] == "M56"
    assert out["external_ids"].get("mag_max") is None or out["external_ids"].get("mag_max") != 17.7
    assert out["external_ids"]["gmag"] == 17.7

    harris = {
        "designation": "M 56",
        "external_ids": {
            "vmag": 8.27,
            "mag_max": 8.27,
            "band_notes": "V integrada (Harris VII/202)",
            "harris": "M 56",
        },
    }
    out2 = _merge_payload(out, harris, "harris")
    assert abs(float(out2["external_ids"]["mag_max"]) - 8.27) < 1e-6
    assert out2["designation"] == "M56" or "56" in out2["designation"]

"""E20 / D-012: registry + providers smoke."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from astrocitizen.domain.observation import Observation, Spectrum
from astrocitizen.integrations import ProviderRegistry, default_providers
from astrocitizen.integrations.aavso import AavsoProvider
from astrocitizen.integrations.bess import BessProvider
from astrocitizen.integrations.mpc import MpcProvider
from astrocitizen.integrations.tns import TnsProvider
from astrocitizen.integrations.vsx import VsxProvider
from astrocitizen.ports.observatory_provider import ObservatoryProvider
from astrocitizen.shared.errors import DomainError, NotFoundError


def test_default_registry_manifests() -> None:
    reg = ProviderRegistry()
    names = reg.list_names()
    assert names == sorted(
        ["aavso", "bess", "gaia", "mpc", "sesame", "simbad", "tns", "vizier", "vsx"]
    )
    manifests = {m["name"]: m["features"] for m in reg.list_manifests()}
    assert "search" in manifests["simbad"]
    assert "search" in manifests["sesame"]
    assert "search" in manifests["vizier"]
    assert "search" in manifests["gaia"]
    assert "prepare_photometry" in manifests["aavso"]
    assert "prepare_astrometry" in manifests["mpc"]
    assert "prepare_spectrum" in manifests["bess"]
    assert "prepare_transient" in manifests["tns"]
    searchers = reg.with_feature("search")
    assert {p.name for p in searchers} >= {
        "simbad",
        "vsx",
        "aavso",
        "sesame",
        "vizier",
        "gaia",
    }


def test_registry_get_unknown() -> None:
    with pytest.raises(NotFoundError):
        ProviderRegistry().get("nope")


def test_providers_are_observatory_provider_protocol() -> None:
    for p in default_providers():
        assert isinstance(p, ObservatoryProvider)


def test_vsx_provider_search_mock() -> None:
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
            assert name == "SS Cyg"
            from astrocitizen.adapters.sky.vsx_resolver import VsxResolver

            return VsxResolver(opener=lambda _u: json.dumps(sample)).resolve(name)

    p = VsxProvider(resolver=Fake())
    out = p.search_object("SS Cyg")
    assert out["external_ids"]["auid"] == "000-BCP-220"


def test_aavso_prepare_from_points(tmp_path: Path) -> None:
    obs = Observation(
        object_name="SS CYG",
        observatory_code="XYZ",
        filter_name="V",
        extra={
            "points": [
                {
                    "t_utc": "2026-07-23T01:00:00Z",
                    "y": 12.1,
                    "y_err": 0.02,
                }
            ]
        },
    )
    path = AavsoProvider().prepare_photometry(obs, out_path=tmp_path / "a.txt")
    text = path.read_text(encoding="utf-8")
    assert "#TYPE=EXTENDED" in text
    assert "SS CYG" in text


def test_aavso_missing_feature_raises() -> None:
    with pytest.raises(DomainError, match="feature"):
        AavsoProvider().prepare_spectrum(
            Spectrum(object_name="x"), out_path=Path("/tmp/x.fits")
        )


def test_mpc_prepare(tmp_path: Path) -> None:
    obs = Observation(
        object_name="2026 AA",
        ra_deg=10.0,
        dec_deg=-5.0,
        observatory_code="XXX",
        mag=18.0,
        filter_name="R",
        extra={"epoch_utc": "2026-07-23T00:00:00Z"},
    )
    path = MpcProvider().prepare_astrometry(obs, out_path=tmp_path / "a.psv")
    assert "observatory=XXX" in path.read_text(encoding="utf-8")


def test_tns_prepare(tmp_path: Path) -> None:
    obs = Observation(
        object_name="AT2026test",
        ra_deg=150.0,
        dec_deg=20.0,
        mag=17.5,
        observer="Obs",
    )
    path = TnsProvider().prepare_transient(
        obs, out_path=tmp_path / "t.json", groupid=48
    )
    data = json.loads(path.read_text(encoding="utf-8"))
    assert "at_report" in data


def test_bess_prepare(tmp_path: Path) -> None:
    wave = np.linspace(400.0, 700.0, 50)
    flux = np.ones(50)
    spec = Spectrum(
        object_name="gam Cas",
        wavelength=list(wave),
        flux=list(flux),
        observer="Obs",
        instrument="Alpy",
    )
    path = BessProvider().prepare_spectrum(
        spec,
        out_path=tmp_path / "s.fits",
        date_obs="2026-07-23T01:00:00",
        exptime_s=120.0,
    )
    assert path.is_file()

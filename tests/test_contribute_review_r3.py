"""Testes R3: prefill Revisar campos TNS / ExoClock / BeSS / IOTA."""

from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

from astrocitizen.desktop.contribute import (
    prefill_bess_fields,
    prefill_exoclock_fields,
    prefill_iota_fields,
    prefill_tns_fields,
)
from astrocitizen.contribution.validate_minimum import validate_product_for_network


def test_prefill_tns_from_product() -> None:
    pid = uuid4()
    product = SimpleNamespace(
        id=pid,
        parameters={},
        summary={"ra_deg": 10.5, "dec_deg": -20.25, "mag": 18.1},
    )

    class Archive:
        def get_analysis_product(self, product_id):
            return product if product_id == pid else None

    filled = prefill_tns_fields(
        Archive(),
        credentials={"groupid": 7},
        current={"product_id": str(pid)},
    )
    assert filled["ra_deg"] == 10.5
    assert filled["dec_deg"] == -20.25
    assert filled["mag"] == 18.1
    assert filled["groupid"] == "7"


def test_prefill_exoclock_from_product() -> None:
    pid = uuid4()
    product = SimpleNamespace(
        id=pid,
        parameters={"target": "WASP-12b"},
        summary={},
    )

    class Archive:
        def get_analysis_product(self, product_id):
            return product if product_id == pid else None

        def list_measurement_points(self, _id):
            return [{"y": 1.0}]

    filled = prefill_exoclock_fields(
        Archive(),
        current={"product_id": str(pid), "target": "TARGET"},
    )
    assert filled["target"] == "WASP-12b"
    r = validate_product_for_network(
        Archive(),
        network="exoclock",
        product_id=pid,
        payload={"target": filled["target"]},
    )
    assert r.ok


def test_prefill_bess_and_iota() -> None:
    pid = uuid4()
    bess = SimpleNamespace(
        id=pid,
        product_type="spectrum_1d",
        parameters={
            "objname": "gam Cas",
            "date_obs": "2026-07-21T01:00:00",
            "spectrum_uri": "file:///x.fits",
            "observer": "SpecObs",
        },
        summary={},
    )
    iota = SimpleNamespace(
        id=pid,
        product_type="occultation_prediction",
        parameters={
            "event_id": "2026-Eur",
            "star": "TYC 1",
            "asteroid": "(1) Ceres",
            "result": "positive",
        },
        summary={},
    )

    class Archive:
        def __init__(self, product):
            self.product = product

        def get_analysis_product(self, product_id):
            return self.product if product_id == pid else None

    b = prefill_bess_fields(
        Archive(bess),
        current={"product_id": str(pid)},
    )
    assert b["objname"] == "gam Cas"
    assert b["date_obs"] == "2026-07-21T01:00:00"
    assert b["observer"] == "SpecObs"

    i = prefill_iota_fields(
        Archive(iota),
        credentials={"observer": "OccObs"},
        current={"product_id": str(pid)},
    )
    assert i["event_id"] == "2026-Eur"
    assert i["star"] == "TYC 1"
    assert i["asteroid"] == "(1) Ceres"
    assert i["observer"] == "OccObs" or i["observer"]


def test_validate_bess_objname_when_in_payload() -> None:
    archive = SimpleNamespace(
        get_analysis_product=lambda _id: None,
        list_measurement_points=lambda _id: [],
    )
    bad = validate_product_for_network(
        archive, network="bess", payload={"objname": "", "observer": "X"}
    )
    assert not bad.ok
    assert any(i.code == "bess_objname" for i in bad.issues)
    good = validate_product_for_network(
        archive, network="bess", payload={"objname": "gam Cas", "observer": "X"}
    )
    assert good.ok

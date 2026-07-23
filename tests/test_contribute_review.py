"""Testes R2: prefill Revisar campos AAVSO/MPC."""

from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

from astrocitizen.desktop.contribute import (
    format_validation_issue_lines,
    prefill_aavso_fields,
    prefill_mpc_fields,
)
from astrocitizen.contribution.validate_minimum import ValidationIssue, ValidationResult


def test_prefill_aavso_from_product_and_creds() -> None:
    pid = uuid4()
    tid = uuid4()
    product = SimpleNamespace(
        id=pid,
        parameters={"target_id": str(tid), "band": "B", "chart": "X12345"},
        summary={},
    )
    target = SimpleNamespace(id=tid, designation="SS CYG")

    class Archive:
        def get_analysis_product(self, product_id):
            return product if product_id == pid else None

        def get_target(self, target_id):
            return target if target_id == tid else None

    filled = prefill_aavso_fields(
        Archive(),
        credentials={"obscode": "XYZ"},
        current={"product_id": str(pid)},
    )
    assert filled["obscode"] == "XYZ"
    assert filled["star"] == "SS CYG"
    assert filled["band"] == "B"
    assert filled["chart"] == "X12345"


def test_prefill_mpc_from_astrometry_product() -> None:
    pid = uuid4()
    product = SimpleNamespace(
        id=pid,
        product_type="astrometry",
        parameters={"designation": "2024 AB1", "band": "V"},
        summary={
            "ra_deg": 123.456,
            "dec_deg": -12.34,
            "epoch_utc": "2026-07-21T02:30:00Z",
            "mag": 18.2,
        },
    )

    class Archive:
        def get_analysis_product(self, product_id):
            return product if product_id == pid else None

    filled = prefill_mpc_fields(
        Archive(),
        credentials={"observatory_code": "XXX", "email": "a@b.c"},
        current={"product_id": str(pid)},
    )
    assert filled["observatory_code"] == "XXX"
    assert filled["designation"] == "2024 AB1"
    assert filled["ra_deg"] == 123.456
    assert filled["dec_deg"] == -12.34
    assert filled["epoch_utc"] == "2026-07-21T02:30:00Z"
    assert filled["mag"] == 18.2
    assert filled["band"] == "V"
    assert filled["email"] == "a@b.c"


def test_format_validation_issue_lines() -> None:
    result = ValidationResult(
        ok=False,
        issues=[
            ValidationIssue(code="aavso_star", message="falta estrela", severity="error"),
            ValidationIssue(code="warn", message="aviso", severity="warning"),
        ],
    )
    lines = format_validation_issue_lines(result)
    assert lines[0].startswith("[error] aavso_star:")
    assert lines[1].startswith("[warning] warn:")

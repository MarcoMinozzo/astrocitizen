"""Programa activo / guia de passos."""

from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

from astrocitizen.programs.guide import (
    normalize_network_key,
    resolve_export_networks,
    step_nav_rows,
    target_link_rows,
)
from astrocitizen.programs.workflows import workflow_for


def test_normalize_network_key() -> None:
    assert normalize_network_key("AAVSO") == "aavso"
    assert normalize_network_key("ExoClock") == "exoclock"
    assert normalize_network_key("ARAS") == "bess"
    assert normalize_network_key("clubes-radio") is None


def test_resolve_export_networks_prefers_program() -> None:
    prog = SimpleNamespace(export_networks=["MPC"])
    wf = {"networks": ["AAVSO"]}
    assert resolve_export_networks(prog, wf) == ["MPC"]
    prog2 = SimpleNamespace(export_networks=[])
    assert resolve_export_networks(prog2, wf) == ["AAVSO"]


def test_step_nav_rows_po_a01() -> None:
    wf = workflow_for("PO-A01")
    assert wf is not None
    rows = step_nav_rows(wf)
    assert rows[0]["step"] == "plan_targets"
    assert rows[0]["area"] == "Configurar"
    export = [r for r in rows if r["step"] == "export_aavso"][0]
    assert export["network"] == "aavso"
    assert export["area"] == "Contribuir"


def test_target_link_rows() -> None:
    tid = uuid4()
    t = SimpleNamespace(id=tid, designation="SS Cyg", target_type="star")
    rows = target_link_rows([(t, "primary", 0)])
    assert rows[0][0] == "SS Cyg"
    assert rows[0][1] == "primary"
    assert rows[0][3] == str(tid)[:8]


def test_program_active_builder() -> None:
    from astrocitizen.desktop.program_active_panel import (
        build_program_active_dashboard,
    )

    assert callable(build_program_active_dashboard)

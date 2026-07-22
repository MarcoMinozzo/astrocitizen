"""U3/U4: arquivo + analyze helpers."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import pytest

from astrocitizen.adapters.sqlite import SqliteArchive
from astrocitizen.desktop.archive_panel import observation_rows, product_rows
from astrocitizen.reduction.models import AnalysisProduct
from astrocitizen.shared.ids import new_id
from astrocitizen.workspace.models import Workspace


def test_observation_rows() -> None:
    rows = observation_rows(
        [
            {
                "observed_at_utc": "2026-07-22T01:00:00Z",
                "simulated": 0,
                "camera_backend": "sim",
                "state": "ready",
                "notes": "n",
                "id": "abcdefgh-ijkl",
            }
        ]
    )
    assert rows[0][1] == "real"
    assert rows[0][5] == "abcdefgh"


def test_product_rows() -> None:
    p = SimpleNamespace(
        product_type="light_curve",
        state="ready",
        summary={"mag": 12.1, "flux": 1.2},
        id=uuid4(),
    )
    rows = product_rows([p])
    assert rows[0][0] == "light_curve"
    assert "mag=" in rows[0][2]


def test_list_analysis_products(tmp_path) -> None:
    from pathlib import Path

    archive = SqliteArchive(Path(tmp_path) / "a.sqlite3")
    archive.migrate()
    ws = archive.upsert_workspace(Workspace(id=new_id(), name="ws"))
    product = AnalysisProduct(
        id=new_id(),
        workspace_id=ws.id,
        program_id=None,
        product_type="radio_timeseries",
        version_num=1,
        is_publishable=False,
        parameters={},
        summary={"n": 3},
        state="ready",
    )
    archive.save_analysis_product(product)
    listed = archive.list_analysis_products(ws.id)
    assert len(listed) == 1
    assert listed[0].product_type == "radio_timeseries"
    typed = archive.list_analysis_products(ws.id, product_type="radio_timeseries")
    assert len(typed) == 1
    empty = archive.list_analysis_products(ws.id, product_type="nope")
    assert empty == []
    archive.close()


def test_analyze_builder() -> None:
    from astrocitizen.desktop.analyze_panel import build_analyze_dashboard
    from astrocitizen.desktop.archive_panel import build_archive_dashboard

    assert callable(build_analyze_dashboard)
    assert callable(build_archive_dashboard)


def test_analyze_astrometry_widgets(tmp_path: Path) -> None:
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication

    from astrocitizen.desktop.analyze_panel import build_analyze_dashboard

    app = QApplication.instance() or QApplication([])
    archive = SqliteArchive(tmp_path / "a.sqlite3")
    archive.migrate()
    Dash = build_analyze_dashboard()
    w = Dash(archive, artifacts_root=tmp_path / "art")
    assert hasattr(w, "as_path")
    assert hasattr(w, "_run_astrometry")
    assert callable(w._run_astrometry)
    _ = app


def test_parse_optional_float() -> None:
    from astrocitizen.desktop.analyze_panel import parse_optional_float

    assert parse_optional_float("") is None
    assert parse_optional_float("  ") is None
    assert parse_optional_float("12.5") == 12.5
    try:
        parse_optional_float("x")
        raise AssertionError("expected ValueError")
    except ValueError:
        pass

"""Testes AAVSO JD + MPC ADES + TNS (dry-run)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

from astrocitizen.adapters.sqlite import SqliteArchive
from astrocitizen.contribution.aavso import format_aavso_extended
from astrocitizen.contribution.credentials import LocalCredentialsStore
from astrocitizen.contribution.models import NetworkSubmission
from astrocitizen.contribution.mpc import MpcAdesSubmitter, format_ades_psv, write_ades_psv
from astrocitizen.contribution.tns import TnsClient, format_tns_at_report, write_tns_report
from astrocitizen.workspace.models import Workspace


def test_aavso_extended_uses_jd() -> None:
    text = format_aavso_extended(
        star_name="SS CYG",
        observer_code="XYZ",
        points=[{"t_utc": "2026-07-21T01:00:00Z", "y": 12.345, "y_err": 0.02}],
        band="V",
    )
    assert "#DATE=JD" in text
    assert "#OBSCODE=XYZ" in text
    line = [ln for ln in text.splitlines() if ln.startswith("SS CYG,")][0]
    parts = line.split(",")
    jd = float(parts[1])
    assert 2460000 < jd < 2470000
    assert parts[2] == "12.3450"


def test_ades_psv_and_dry_run(tmp_path: Path) -> None:
    psv = format_ades_psv(
        observatory_code="XXX",
        designation="2026 AB1",
        observations=[
            {
                "epoch_utc": "2026-07-21T02:30:00Z",
                "ra_deg": 150.1,
                "dec_deg": -20.2,
                "mag": 18.5,
                "band": "V",
                "ra_err_arcsec": 0.5,
                "dec_err_arcsec": 0.5,
            }
        ],
    )
    assert "permID|provID|obsTime" in psv
    assert "2026 AB1" in psv
    path = write_ades_psv(
        tmp_path / "neo.psv",
        observatory_code="XXX",
        designation="2026 AB1",
        observations=[
            {
                "epoch_utc": "2026-07-21T02:30:00Z",
                "ra_deg": 150.1,
                "dec_deg": -20.2,
            }
        ],
    )
    meta = MpcAdesSubmitter().submit(path, email="a@b.c", dry_run=True)
    assert meta["status"] == "dry_run"


def test_tns_at_report_dry_run(tmp_path: Path) -> None:
    report = format_tns_at_report(
        ra_deg=10.0,
        dec_deg=20.0,
        groupid=48,
        reporter="AstroCitizen Test",
        discovery_mag=19.2,
    )
    assert "at_report" in report
    path = write_tns_report(tmp_path / "at.json", report)
    assert path.is_file()
    client = TnsClient(api_key="k", user_id="1", sandbox=True)
    meta = client.submit_report(report, dry_run=True)
    assert meta["status"] == "dry_run"
    assert meta["sandbox"] is True


def test_credentials_and_submissions(tmp_path: Path) -> None:
    cred = LocalCredentialsStore(tmp_path / "credentials.json")
    cred.set_network("aavso", {"obscode": "ABC"})
    assert cred.get_network("aavso")["obscode"] == "ABC"

    db = tmp_path / "t.sqlite3"
    archive = SqliteArchive(db)
    archive.migrate()
    ws = archive.upsert_workspace(Workspace(id=uuid4(), name="w"))
    sub = NetworkSubmission(
        id=uuid4(),
        workspace_id=ws.id,
        network="aavso",
        status="dry_run",
        payload_summary={"star": "SS CYG"},
    )
    archive.save_network_submission(sub)
    got = archive.get_network_submission(sub.id)
    assert got is not None and got.network == "aavso"
    assert len(archive.list_network_submissions(ws.id)) == 1
    archive.close()


def test_mpc_submit_http_mock(tmp_path: Path) -> None:
    path = write_ades_psv(
        tmp_path / "x.psv",
        observatory_code="XXX",
        designation="2026 AB1",
        observations=[{"epoch_utc": "2026-07-21T00:00:00Z", "ra_deg": 1.0, "dec_deg": 2.0}],
    )

    class Resp:
        status = 200

        def read(self) -> bytes:
            return b"OK ACK"

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    with patch("astrocitizen.contribution.mpc.urlopen", return_value=Resp()):
        meta = MpcAdesSubmitter().submit(path, email="a@b.c", dry_run=False)
    assert meta["status"] == "submitted"
    assert "OK" in meta["response"]

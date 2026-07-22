"""Radio cidada (PO-I*): import potencia vs tempo (IN-RAD)."""

from __future__ import annotations

import csv
import io
from pathlib import Path
from typing import Any
from uuid import UUID

from astrocitizen.adapters.fs import LocalArtifactStore
from astrocitizen.reduction.models import AnalysisProduct
from astrocitizen.shared.errors import DomainError
from astrocitizen.shared.ids import new_id
from astrocitizen.shared.timeutil import utc_now_iso


def parse_radio_power_csv(path: Path) -> list[dict[str, Any]]:
    """CSV t_utc,power[,power_err] ou time,intensity."""
    path = Path(path)
    if not path.is_file():
        raise DomainError(f"CSV radio nao encontrado: {path}")
    text = path.read_text(encoding="utf-8", errors="replace")
    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        raise DomainError("CSV radio sem cabecalho")
    fields = {(f or "").strip().lower(): f for f in reader.fieldnames}
    t_key = fields.get("t_utc") or fields.get("time") or fields.get("utc") or fields.get("t")
    y_key = (
        fields.get("power")
        or fields.get("y")
        or fields.get("intensity")
        or fields.get("flux")
        or fields.get("dbm")
        or fields.get("adu")
    )
    e_key = fields.get("power_err") or fields.get("y_err") or fields.get("err")
    if not t_key or not y_key:
        raise DomainError("CSV radio precisa t_utc/time e power/intensity")
    points: list[dict[str, Any]] = []
    for i, row in enumerate(reader):
        t = (row.get(t_key) or "").strip()
        if not t:
            continue
        try:
            y = float(row.get(y_key) or "")
        except ValueError as exc:
            raise DomainError(f"radio linha {i+1}: power invalido") from exc
        err = None
        if e_key and row.get(e_key):
            try:
                err = float(row[e_key])
            except ValueError:
                err = None
        points.append(
            {
                "id": str(new_id()),
                "t_utc": t,
                "sequence_index": i,
                "x": float(i),
                "y": y,
                "y_err": err,
                "band": "radio",
                "meta": {},
            }
        )
    if len(points) < 2:
        raise DomainError("serie radio com menos de 2 pontos")
    return points


def parse_radio_power_hdf5(path: Path) -> list[dict[str, Any]]:
    """HDF5 opcional: datasets time (str/float) + power."""
    path = Path(path)
    if not path.is_file():
        raise DomainError(f"HDF5 nao encontrado: {path}")
    try:
        import h5py  # type: ignore
        import numpy as np
    except ImportError as exc:
        raise DomainError(
            "HDF5 requer pacote h5py (pip install h5py). Use CSV entretanto."
        ) from exc
    with h5py.File(path, "r") as h5:
        # try common names
        t_ds = None
        p_ds = None
        for name in ("t_utc", "time", "times", "t"):
            if name in h5:
                t_ds = h5[name]
                break
        for name in ("power", "intensity", "flux", "y", "data"):
            if name in h5:
                p_ds = h5[name]
                break
        if t_ds is None or p_ds is None:
            # first two datasets
            keys = [k for k in h5.keys() if hasattr(h5[k], "shape")]
            if len(keys) < 2:
                raise DomainError("HDF5 sem datasets time/power reconheciveis")
            t_ds, p_ds = h5[keys[0]], h5[keys[1]]
        t_arr = np.asarray(t_ds)
        p_arr = np.asarray(p_ds, dtype=float).ravel()
        if t_arr.shape[0] != p_arr.shape[0]:
            raise DomainError("HDF5 time/power com tamanhos diferentes")
        points: list[dict[str, Any]] = []
        for i, (t, y) in enumerate(zip(t_arr, p_arr, strict=True)):
            if hasattr(t, "decode"):
                t_s = t.decode("utf-8", errors="replace")
            else:
                t_s = str(t)
            points.append(
                {
                    "id": str(new_id()),
                    "t_utc": t_s,
                    "sequence_index": i,
                    "x": float(i),
                    "y": float(y),
                    "y_err": None,
                    "band": "radio",
                    "meta": {},
                }
            )
    if len(points) < 2:
        raise DomainError("serie radio HDF5 com menos de 2 pontos")
    return points


class ImportRadioTimeseries:
    """IN-RAD: Observation + radio_timeseries + measurement_points."""

    def __init__(self, archive: Any, store: LocalArtifactStore) -> None:
        self.archive = archive
        self.store = store

    def execute(
        self,
        *,
        workspace_id: UUID,
        path: Path,
        site_id: UUID | None = None,
        program_id: UUID | None = None,
        observer: str = "AstroCitizen",
        frequency_mhz: float | None = None,
        notes: str = "",
        observed_at_utc: str | None = None,
    ) -> AnalysisProduct:
        path = Path(path)
        if not path.is_file():
            raise DomainError(f"ficheiro radio nao encontrado: {path}")
        suf = path.suffix.lower()
        if suf in (".csv", ".txt"):
            points = parse_radio_power_csv(path)
            fmt = "csv"
        elif suf in (".h5", ".hdf5", ".hdf"):
            points = parse_radio_power_hdf5(path)
            fmt = "hdf5"
        else:
            raise DomainError("radio: use .csv/.txt ou .h5/.hdf5")

        uri = self.store.put(path, key=f"import/radio/{path.name}")
        when = observed_at_utc or str(points[0]["t_utc"]) or utc_now_iso()
        obs_id = new_id()
        self.archive.create_observation(
            observation_id=obs_id,
            workspace_id=workspace_id,
            observed_at_utc=when,
            site_id=site_id,
            program_id=program_id,
            simulated=False,
            notes=f"radio:{path.name}",
        )
        self.archive.save_artifact(
            artifact_id=new_id(),
            workspace_id=workspace_id,
            kind="radio_timeseries",
            uri=uri,
            filename=path.name,
            observation_id=obs_id,
            size_bytes=path.stat().st_size,
        )
        ys = [float(p["y"]) for p in points]
        product = AnalysisProduct(
            id=new_id(),
            workspace_id=workspace_id,
            program_id=program_id,
            product_type="radio_timeseries",
            version_num=1,
            is_publishable=False,
            parameters={
                "channel": "IN-RAD",
                "source_uri": uri,
                "source_format": fmt,
                "observer": observer,
                "frequency_mhz": frequency_mhz,
                "notes": notes,
                "site_id": str(site_id) if site_id else None,
                "observation_id": str(obs_id),
                "n_points": len(points),
            },
            summary={
                "n_points": len(points),
                "t0": points[0]["t_utc"],
                "t1": points[-1]["t_utc"],
                "power_min": min(ys),
                "power_max": max(ys),
                "power_med": sorted(ys)[len(ys) // 2],
                "frequency_mhz": frequency_mhz,
                "format": fmt,
            },
            state="ready",
        )
        product = self.archive.save_analysis_product(product)
        self.archive.link_product_observation(product.id, obs_id)
        self.archive.save_measurement_points(product.id, points)
        return product

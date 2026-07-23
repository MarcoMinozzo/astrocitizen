"""Radio cidada (PO-I*): serie / espectro / drift (IN-RAD, AC-160/161)."""

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
    """CSV t_utc,power[,power_err] ou time,intensity (PO-I01)."""
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


def parse_radio_spectrum_csv(path: Path) -> list[dict[str, Any]]:
    """CSV freq_mhz,power[,power_err] (PO-I02)."""
    path = Path(path)
    if not path.is_file():
        raise DomainError(f"CSV espectro radio nao encontrado: {path}")
    text = path.read_text(encoding="utf-8", errors="replace")
    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        raise DomainError("CSV espectro sem cabecalho")
    fields = {(f or "").strip().lower(): f for f in reader.fieldnames}
    f_key = (
        fields.get("freq_mhz")
        or fields.get("frequency")
        or fields.get("freq")
        or fields.get("mhz")
        or fields.get("f")
    )
    y_key = (
        fields.get("power")
        or fields.get("y")
        or fields.get("intensity")
        or fields.get("flux")
        or fields.get("dbm")
        or fields.get("adu")
    )
    e_key = fields.get("power_err") or fields.get("y_err") or fields.get("err")
    t_key = fields.get("t_utc") or fields.get("time") or fields.get("utc")
    if not f_key or not y_key:
        raise DomainError("CSV espectro precisa freq_mhz/freq e power/intensity")
    points: list[dict[str, Any]] = []
    for i, row in enumerate(reader):
        try:
            freq = float(row.get(f_key) or "")
            y = float(row.get(y_key) or "")
        except ValueError as exc:
            raise DomainError(f"espectro linha {i+1}: valores invalidos") from exc
        err = None
        if e_key and row.get(e_key):
            try:
                err = float(row[e_key])
            except ValueError:
                err = None
        t = ""
        if t_key:
            t = (row.get(t_key) or "").strip()
        points.append(
            {
                "id": str(new_id()),
                "t_utc": t or utc_now_iso(),
                "sequence_index": i,
                "x": freq,
                "y": y,
                "y_err": err,
                "band": "radio",
                "meta": {"freq_mhz": freq, "channel": i},
            }
        )
    if len(points) < 2:
        raise DomainError("espectro radio com menos de 2 pontos")
    return points


def parse_radio_scan_csv(path: Path) -> list[dict[str, Any]]:
    """CSV t_utc,power[,az_deg|el_deg|ha_deg][,power_err] (PO-I03)."""
    path = Path(path)
    if not path.is_file():
        raise DomainError(f"CSV scan radio nao encontrado: {path}")
    text = path.read_text(encoding="utf-8", errors="replace")
    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        raise DomainError("CSV scan sem cabecalho")
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
    az_key = fields.get("az_deg") or fields.get("az") or fields.get("azimuth")
    el_key = fields.get("el_deg") or fields.get("el") or fields.get("elevation") or fields.get("alt")
    ha_key = fields.get("ha_deg") or fields.get("ha") or fields.get("hour_angle")
    if not t_key or not y_key:
        raise DomainError("CSV scan precisa t_utc/time e power/intensity")
    points: list[dict[str, Any]] = []
    for i, row in enumerate(reader):
        t = (row.get(t_key) or "").strip()
        if not t:
            continue
        try:
            y = float(row.get(y_key) or "")
        except ValueError as exc:
            raise DomainError(f"scan linha {i+1}: power invalido") from exc
        err = None
        if e_key and row.get(e_key):
            try:
                err = float(row[e_key])
            except ValueError:
                err = None
        meta: dict[str, Any] = {}
        for key, src in (("az_deg", az_key), ("el_deg", el_key), ("ha_deg", ha_key)):
            if not src or not row.get(src):
                continue
            try:
                meta[key] = float(row[src])
            except ValueError:
                pass
        points.append(
            {
                "id": str(new_id()),
                "t_utc": t,
                "sequence_index": i,
                "x": float(i),
                "y": y,
                "y_err": err,
                "band": "radio",
                "meta": meta,
            }
        )
    if len(points) < 2:
        raise DomainError("scan radio com menos de 2 pontos")
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


def _persist_radio(
    archive: Any,
    store: LocalArtifactStore,
    *,
    workspace_id: UUID,
    path: Path,
    points: list[dict[str, Any]],
    product_type: str,
    fmt: str,
    site_id: UUID | None,
    program_id: UUID | None,
    observer: str,
    frequency_mhz: float | None,
    notes: str,
    lab_notes: str,
    observed_at_utc: str | None,
    extra_summary: dict[str, Any] | None = None,
) -> AnalysisProduct:
    uri = store.put(path, key=f"import/radio/{path.name}")
    when = observed_at_utc or str(points[0].get("t_utc") or "") or utc_now_iso()
    obs_id = new_id()
    archive.create_observation(
        observation_id=obs_id,
        workspace_id=workspace_id,
        observed_at_utc=when,
        site_id=site_id,
        program_id=program_id,
        simulated=False,
        notes=f"radio:{product_type}:{path.name}",
    )
    archive.save_artifact(
        artifact_id=new_id(),
        workspace_id=workspace_id,
        kind=product_type,
        uri=uri,
        filename=path.name,
        observation_id=obs_id,
        size_bytes=path.stat().st_size,
    )
    ys = [float(p["y"]) for p in points]
    xs = [float(p["x"]) for p in points]
    summary: dict[str, Any] = {
        "n_points": len(points),
        "power_min": min(ys),
        "power_max": max(ys),
        "power_med": sorted(ys)[len(ys) // 2],
        "frequency_mhz": frequency_mhz,
        "format": fmt,
        "kind": product_type,
    }
    if product_type == "radio_spectrum":
        summary["freq0_mhz"] = min(xs)
        summary["freq1_mhz"] = max(xs)
        summary["t0"] = points[0]["t_utc"]
    else:
        summary["t0"] = points[0]["t_utc"]
        summary["t1"] = points[-1]["t_utc"]
    if extra_summary:
        summary.update(extra_summary)
    product = AnalysisProduct(
        id=new_id(),
        workspace_id=workspace_id,
        program_id=program_id,
        product_type=product_type,
        version_num=1,
        is_publishable=False,
        parameters={
            "channel": "IN-RAD",
            "source_uri": uri,
            "source_format": fmt,
            "observer": observer,
            "frequency_mhz": frequency_mhz,
            "notes": notes,
            "lab_notes": lab_notes or None,
            "site_id": str(site_id) if site_id else None,
            "observation_id": str(obs_id),
            "n_points": len(points),
            "kind": product_type,
        },
        summary=summary,
        state="ready",
    )
    product = archive.save_analysis_product(product)
    archive.link_product_observation(product.id, obs_id)
    archive.save_measurement_points(product.id, points)
    return product


class ImportRadioTimeseries:
    """IN-RAD: Observation + radio_timeseries + measurement_points (PO-I01/I04)."""

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
        lab_notes: str = "",
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
            raise DomainError("radio series: use .csv/.txt ou .h5/.hdf5")
        return _persist_radio(
            self.archive,
            self.store,
            workspace_id=workspace_id,
            path=path,
            points=points,
            product_type="radio_timeseries",
            fmt=fmt,
            site_id=site_id,
            program_id=program_id,
            observer=observer,
            frequency_mhz=frequency_mhz,
            notes=notes,
            lab_notes=lab_notes,
            observed_at_utc=observed_at_utc,
        )


class ImportRadioSpectrum:
    """IN-RAD: espectro RF CSV -> radio_spectrum (PO-I02)."""

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
        lab_notes: str = "",
        observed_at_utc: str | None = None,
    ) -> AnalysisProduct:
        path = Path(path)
        if not path.is_file():
            raise DomainError(f"ficheiro espectro nao encontrado: {path}")
        if path.suffix.lower() not in (".csv", ".txt"):
            raise DomainError("radio spectrum: use .csv/.txt")
        points = parse_radio_spectrum_csv(path)
        return _persist_radio(
            self.archive,
            self.store,
            workspace_id=workspace_id,
            path=path,
            points=points,
            product_type="radio_spectrum",
            fmt="csv",
            site_id=site_id,
            program_id=program_id,
            observer=observer,
            frequency_mhz=frequency_mhz,
            notes=notes,
            lab_notes=lab_notes,
            observed_at_utc=observed_at_utc,
        )


class ImportRadioScan:
    """IN-RAD: drift/scan CSV -> radio_scan (PO-I03)."""

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
        lab_notes: str = "",
        observed_at_utc: str | None = None,
    ) -> AnalysisProduct:
        path = Path(path)
        if not path.is_file():
            raise DomainError(f"ficheiro scan nao encontrado: {path}")
        if path.suffix.lower() not in (".csv", ".txt"):
            raise DomainError("radio scan: use .csv/.txt")
        points = parse_radio_scan_csv(path)
        with_pointing = sum(1 for p in points if p.get("meta"))
        return _persist_radio(
            self.archive,
            self.store,
            workspace_id=workspace_id,
            path=path,
            points=points,
            product_type="radio_scan",
            fmt="csv",
            site_id=site_id,
            program_id=program_id,
            observer=observer,
            frequency_mhz=frequency_mhz,
            notes=notes,
            lab_notes=lab_notes,
            observed_at_utc=observed_at_utc,
            extra_summary={"n_with_pointing": with_pointing},
        )

"""Especialidades P4 (ENTRADA #7): echelle, speckle, polarimetria."""

from __future__ import annotations

import csv
import io
import math
from pathlib import Path
from typing import Any
from uuid import UUID

from astropy.io import fits

from astrocitizen.adapters.fs import LocalArtifactStore
from astrocitizen.observatory.import_fits import FITS_SUFFIXES, discover_fits_paths
from astrocitizen.reduction.models import AnalysisProduct
from astrocitizen.shared.errors import DomainError
from astrocitizen.shared.ids import new_id
from astrocitizen.shared.timeutil import utc_now_iso

SPECKLE_VIDEO = {".ser", ".avi", ".mp4", ".mov", ".mkv"}


def _observed_from_hdr(hdr: fits.Header) -> str:
    for key in ("DATE-OBS", "DATE", "TIME-OBS"):
        if key in hdr and hdr[key]:
            return str(hdr[key]).replace("/", "-")
    return utc_now_iso()


def _mean_adu(data: Any) -> float:
    import numpy as np

    arr = np.asarray(data, dtype=float)
    if arr.size == 0:
        return 0.0
    return float(np.nanmean(arr))


def discover_echelle_paths(path: Path) -> list[Path]:
    """Ficheiro FITS (multi-ext) ou directorio de ordens."""
    path = Path(path).expanduser().resolve()
    if path.is_file():
        if path.suffix.lower() not in FITS_SUFFIXES:
            raise DomainError(f"echelle: nao e FITS: {path}")
        return [path]
    return discover_fits_paths(path, recursive=False)


def inspect_echelle(path: Path) -> dict[str, Any]:
    """Conta ordens (extensoes com dados 1D/2D) e metadados basicos."""
    path = Path(path)
    with fits.open(path, memmap=False) as hdul:
        orders: list[dict[str, Any]] = []
        for i, hdu in enumerate(hdul):
            data = hdu.data
            if data is None:
                continue
            shape = tuple(int(x) for x in getattr(data, "shape", ()))
            if not shape:
                continue
            hdr = hdu.header
            orders.append(
                {
                    "ext": i,
                    "name": hdu.name or f"EXT{i}",
                    "shape": list(shape),
                    "order": hdr.get("ORDER") or hdr.get("ECORD") or i,
                    "wave_min": _float_hdr(hdr, ("CRVAL1", "WAVELMIN", "WMIN")),
                    "wave_max": _float_hdr(hdr, ("WAVELMAX", "WMAX")),
                }
            )
        if not orders:
            raise DomainError(f"echelle sem extensoes de dados: {path}")
        when = _observed_from_hdr(hdul[0].header)
    return {
        "n_orders": len(orders),
        "orders": orders,
        "observed_at_utc": when,
        "object": str(fits.getheader(path).get("OBJECT") or ""),
    }


def inspect_speckle(path: Path) -> dict[str, Any]:
    """FITS cubo (NAXIS=3), pasta de frames, ou video SER/AVI."""
    path = Path(path).expanduser().resolve()
    if path.is_file() and path.suffix.lower() in SPECKLE_VIDEO:
        return {
            "format": "video",
            "n_frames": None,
            "shape": None,
            "paths": [str(path)],
            "observed_at_utc": utc_now_iso(),
        }
    if path.is_file() and path.suffix.lower() in FITS_SUFFIXES:
        with fits.open(path, memmap=False) as hdul:
            data = hdul[0].data
            if data is None:
                raise DomainError("speckle FITS sem dados no primary HDU")
            shape = tuple(int(x) for x in data.shape)
            n_frames = int(shape[0]) if len(shape) >= 3 else 1
            return {
                "format": "fits_cube" if len(shape) >= 3 else "fits_frame",
                "n_frames": n_frames,
                "shape": list(shape),
                "paths": [str(path)],
                "observed_at_utc": _observed_from_hdr(hdul[0].header),
            }
    if path.is_dir():
        frames = discover_fits_paths(path, recursive=False)
        if len(frames) < 2:
            raise DomainError("speckle pasta precisa de >=2 FITS")
        with fits.open(frames[0], memmap=False) as hdul:
            data = hdul[0].data
            shape = list(data.shape) if data is not None else []
            when = _observed_from_hdr(hdul[0].header)
        return {
            "format": "fits_stack",
            "n_frames": len(frames),
            "shape": shape,
            "paths": [str(p) for p in frames],
            "observed_at_utc": when,
        }
    raise DomainError("speckle: use FITS cubo, pasta FITS ou SER/AVI")


def parse_polar_angles_csv(path: Path) -> dict[str, float]:
    """CSV filename,angle_deg (ou file,polang)."""
    text = Path(path).read_text(encoding="utf-8", errors="replace")
    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        raise DomainError("CSV polar sem cabecalho")
    fields = {(f or "").strip().lower(): f for f in reader.fieldnames}
    f_key = fields.get("filename") or fields.get("file") or fields.get("name")
    a_key = fields.get("angle_deg") or fields.get("polang") or fields.get("angle")
    if not f_key or not a_key:
        raise DomainError("CSV polar precisa filename + angle_deg")
    out: dict[str, float] = {}
    for row in reader:
        name = (row.get(f_key) or "").strip()
        if not name:
            continue
        try:
            out[name] = float(row[a_key])
        except (TypeError, ValueError) as exc:
            raise DomainError(f"angulo invalido para {name}") from exc
    if not out:
        raise DomainError("CSV polar vazio")
    return out


def collect_polar_frames(
    path: Path, angles_map: dict[str, float] | None = None
) -> list[dict[str, Any]]:
    """Lista frames com angulo (header POLANG ou CSV)."""
    path = Path(path).expanduser().resolve()
    if path.is_file() and path.suffix.lower() in FITS_SUFFIXES:
        files = [path]
    elif path.is_dir():
        files = discover_fits_paths(path, recursive=False)
    else:
        raise DomainError("polar: ficheiro FITS ou directorio")
    if len(files) < 2:
        raise DomainError("polarimetria precisa de >=2 frames")

    frames: list[dict[str, Any]] = []
    for fp in files:
        with fits.open(fp, memmap=False) as hdul:
            hdr = hdul[0].header
            data = hdul[0].data
            if data is None:
                continue
            ang = None
            if angles_map and fp.name in angles_map:
                ang = angles_map[fp.name]
            else:
                ang = _float_hdr(hdr, ("POLANG", "POLARANG", "ANGLE"))
            if ang is None:
                raise DomainError(
                    f"frame sem angulo: {fp.name} (POLANG header ou CSV)"
                )
            frames.append(
                {
                    "filename": fp.name,
                    "path": str(fp),
                    "angle_deg": float(ang),
                    "mean_adu": _mean_adu(data),
                    "observed_at_utc": _observed_from_hdr(hdr),
                }
            )
    if len(frames) < 2:
        raise DomainError("polarimetria: <2 frames validos")
    return frames


def estimate_stokes(frames: list[dict[str, Any]]) -> dict[str, float | None]:
    """Stokes I/Q/U a partir de intensidades medias perto de 0/45/90/135."""
    by_ang: dict[int, float] = {}
    for fr in frames:
        key = int(round(float(fr["angle_deg"])) % 180)
        # nearest canonical
        canon = min((0, 45, 90, 135), key=lambda c: abs(c - key))
        if abs(canon - key) <= 5:
            by_ang[canon] = float(fr["mean_adu"])
    i0 = by_ang.get(0)
    i45 = by_ang.get(45)
    i90 = by_ang.get(90)
    i135 = by_ang.get(135)
    if None in (i0, i45, i90, i135):
        return {
            "I": None,
            "Q": None,
            "U": None,
            "P": None,
            "theta_deg": None,
            "complete_set": False,
        }
    assert i0 is not None and i45 is not None and i90 is not None and i135 is not None
    i_tot = 0.5 * (i0 + i45 + i90 + i135)
    q = i0 - i90
    u = i45 - i135
    if i_tot == 0:
        return {
            "I": 0.0,
            "Q": q,
            "U": u,
            "P": None,
            "theta_deg": None,
            "complete_set": True,
        }
    p = math.sqrt(q * q + u * u) / i_tot
    theta = 0.5 * math.degrees(math.atan2(u, q))
    return {
        "I": i_tot,
        "Q": q,
        "U": u,
        "P": p,
        "theta_deg": theta,
        "complete_set": True,
    }


def _float_hdr(hdr: fits.Header, keys: tuple[str, ...]) -> float | None:
    for k in keys:
        if k in hdr and hdr[k] is not None and hdr[k] != "":
            try:
                return float(hdr[k])
            except (TypeError, ValueError):
                continue
    return None


class ImportEchelleOrders:
    """PO-B07 / IN-SPEC: multi-order FITS -> product echelle_orders."""

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
        notes: str = "",
    ) -> AnalysisProduct:
        files = discover_echelle_paths(Path(path))
        infos = [inspect_echelle(p) for p in files]
        n_orders = sum(int(i["n_orders"]) for i in infos)
        when = infos[0]["observed_at_utc"]
        obs_id = new_id()
        self.archive.create_observation(
            observation_id=obs_id,
            workspace_id=workspace_id,
            observed_at_utc=when,
            site_id=site_id,
            program_id=program_id,
            simulated=False,
            notes=f"echelle:{files[0].name}",
        )
        uris: list[str] = []
        for fp in files:
            uri = self.store.put(fp, key=f"import/echelle/{fp.name}")
            uris.append(uri)
            self.archive.save_artifact(
                artifact_id=new_id(),
                workspace_id=workspace_id,
                kind="echelle_orders",
                uri=uri,
                filename=fp.name,
                observation_id=obs_id,
                size_bytes=fp.stat().st_size,
            )
        product = AnalysisProduct(
            id=new_id(),
            workspace_id=workspace_id,
            program_id=program_id,
            product_type="echelle_orders",
            version_num=1,
            is_publishable=False,
            parameters={
                "channel": "IN-SPEC",
                "template": "PO-B07",
                "observer": observer,
                "notes": notes,
                "site_id": str(site_id) if site_id else None,
                "observation_id": str(obs_id),
                "source_uris": uris,
                "files": [str(p) for p in files],
                "inspections": infos,
            },
            summary={
                "n_files": len(files),
                "n_orders": n_orders,
                "object": infos[0].get("object") or "",
            },
            state="ready",
        )
        product = self.archive.save_analysis_product(product)
        self.archive.link_product_observation(product.id, obs_id)
        return product


class ImportSpeckleCube:
    """PO-G02 / IN-IMP: cubo/stack/video -> product speckle_cube."""

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
        notes: str = "",
    ) -> AnalysisProduct:
        info = inspect_speckle(Path(path))
        paths = [Path(p) for p in info["paths"]]
        when = info["observed_at_utc"]
        obs_id = new_id()
        self.archive.create_observation(
            observation_id=obs_id,
            workspace_id=workspace_id,
            observed_at_utc=when,
            site_id=site_id,
            program_id=program_id,
            simulated=False,
            notes=f"speckle:{paths[0].name}",
        )
        uris: list[str] = []
        for fp in paths:
            uri = self.store.put(fp, key=f"import/speckle/{fp.name}")
            uris.append(uri)
            kind = "video_ser" if fp.suffix.lower() == ".ser" else "speckle_cube"
            if fp.suffix.lower() in SPECKLE_VIDEO and fp.suffix.lower() != ".ser":
                kind = "video_occ"
            self.archive.save_artifact(
                artifact_id=new_id(),
                workspace_id=workspace_id,
                kind=kind,
                uri=uri,
                filename=fp.name,
                observation_id=obs_id,
                size_bytes=fp.stat().st_size,
            )
        product = AnalysisProduct(
            id=new_id(),
            workspace_id=workspace_id,
            program_id=program_id,
            product_type="speckle_cube",
            version_num=1,
            is_publishable=False,
            parameters={
                "channel": "IN-IMP",
                "template": "PO-G02",
                "observer": observer,
                "notes": notes,
                "site_id": str(site_id) if site_id else None,
                "observation_id": str(obs_id),
                "source_uris": uris,
                "format": info["format"],
                "shape": info.get("shape"),
            },
            summary={
                "n_frames": info.get("n_frames"),
                "format": info["format"],
                "n_files": len(paths),
            },
            state="ready",
        )
        product = self.archive.save_analysis_product(product)
        self.archive.link_product_observation(product.id, obs_id)
        return product


class ImportPolarimetrySet:
    """PO-H01: set polarizador + Stokes estimado -> polarimetry_stokes."""

    def __init__(self, archive: Any, store: LocalArtifactStore) -> None:
        self.archive = archive
        self.store = store

    def execute(
        self,
        *,
        workspace_id: UUID,
        path: Path,
        angles_csv: Path | None = None,
        site_id: UUID | None = None,
        program_id: UUID | None = None,
        observer: str = "AstroCitizen",
        notes: str = "",
    ) -> AnalysisProduct:
        angles_map = None
        if angles_csv is not None:
            angles_map = parse_polar_angles_csv(Path(angles_csv))
        frames = collect_polar_frames(Path(path), angles_map)
        stokes = estimate_stokes(frames)
        when = frames[0]["observed_at_utc"]
        obs_id = new_id()
        self.archive.create_observation(
            observation_id=obs_id,
            workspace_id=workspace_id,
            observed_at_utc=when,
            site_id=site_id,
            program_id=program_id,
            simulated=False,
            notes=f"polar:{len(frames)}frames",
        )
        uris: list[str] = []
        for fr in frames:
            fp = Path(fr["path"])
            uri = self.store.put(fp, key=f"import/polar/{fp.name}")
            uris.append(uri)
            self.archive.save_artifact(
                artifact_id=new_id(),
                workspace_id=workspace_id,
                kind="polar_frame",
                uri=uri,
                filename=fp.name,
                observation_id=obs_id,
                size_bytes=fp.stat().st_size,
            )
        if angles_csv is not None:
            ac = Path(angles_csv)
            auri = self.store.put(ac, key=f"import/polar/{ac.name}")
            self.archive.save_artifact(
                artifact_id=new_id(),
                workspace_id=workspace_id,
                kind="polar_angles",
                uri=auri,
                filename=ac.name,
                observation_id=obs_id,
                size_bytes=ac.stat().st_size,
            )
        points = [
            {
                "id": str(new_id()),
                "t_utc": fr["observed_at_utc"],
                "sequence_index": i,
                "x": float(fr["angle_deg"]),
                "y": float(fr["mean_adu"]),
                "y_err": None,
                "band": "polar",
                "meta": {"filename": fr["filename"]},
            }
            for i, fr in enumerate(frames)
        ]
        product = AnalysisProduct(
            id=new_id(),
            workspace_id=workspace_id,
            program_id=program_id,
            product_type="polarimetry_stokes",
            version_num=1,
            is_publishable=False,
            parameters={
                "channel": "IN-IMP",
                "template": "PO-H01",
                "observer": observer,
                "notes": notes,
                "site_id": str(site_id) if site_id else None,
                "observation_id": str(obs_id),
                "source_uris": uris,
                "frames": [
                    {
                        "filename": f["filename"],
                        "angle_deg": f["angle_deg"],
                        "mean_adu": f["mean_adu"],
                    }
                    for f in frames
                ],
                "stokes": stokes,
            },
            summary={
                "n_frames": len(frames),
                "complete_set": stokes.get("complete_set"),
                "P": stokes.get("P"),
                "theta_deg": stokes.get("theta_deg"),
                "I": stokes.get("I"),
            },
            state="ready",
        )
        product = self.archive.save_analysis_product(product)
        self.archive.link_product_observation(product.id, obs_id)
        self.archive.save_measurement_points(product.id, points)
        return product

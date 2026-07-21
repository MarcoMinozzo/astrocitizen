"""Analise solar luz branca / manchas (esqueleto PO-E03 / AC-088)."""

from __future__ import annotations

from typing import Any
from uuid import UUID

import numpy as np
from astropy.io import fits

from astrocitizen.adapters.fs import LocalArtifactStore
from astrocitizen.reduction.models import AnalysisProduct
from astrocitizen.shared.errors import DomainError
from astrocitizen.shared.ids import new_id
from astrocitizen.shared.timeutil import utc_now_iso

REQUIRED_SAFETY_FLAGS = (
    "filter_confirmed",
    "no_unfiltered_eyepiece",
    "daytime_acknowledged",
)


def validate_solar_safety(
    *,
    filter_confirmed: bool,
    no_unfiltered_eyepiece: bool,
    daytime_acknowledged: bool,
    filter_name: str | None = None,
) -> dict[str, Any]:
    """Valida checklist de seguranca; levanta DomainError se incompleto."""
    missing = []
    if not filter_confirmed:
        missing.append("filter_confirmed")
    if not no_unfiltered_eyepiece:
        missing.append("no_unfiltered_eyepiece")
    if not daytime_acknowledged:
        missing.append("daytime_acknowledged")
    if missing:
        raise DomainError(
            "checklist solar incompleto: "
            + ",".join(missing)
            + " (NUNCA observe o Sol sem filtro adequado)"
        )
    return {
        "filter_confirmed": True,
        "no_unfiltered_eyepiece": True,
        "daytime_acknowledged": True,
        "filter_name": filter_name or "white-light",
        "warning": "Solar observing requires a certified solar filter / projection.",
    }


def wolf_number(*, groups: int, spots: int, k: float = 1.0) -> float:
    """Numero de Wolf R = k*(10*g + s)."""
    if groups < 0 or spots < 0:
        raise DomainError("groups/spots devem ser >= 0")
    if k <= 0:
        raise DomainError("k deve ser > 0")
    return float(k) * (10.0 * float(groups) + float(spots))


def _label_components(mask: np.ndarray) -> tuple[np.ndarray, int]:
    """Connected components 4-vizinhos (sem scipy)."""
    h, w = mask.shape
    labels = np.zeros((h, w), dtype=np.int32)
    n = 0
    for y in range(h):
        for x in range(w):
            if not mask[y, x] or labels[y, x]:
                continue
            n += 1
            stack = [(y, x)]
            labels[y, x] = n
            while stack:
                cy, cx = stack.pop()
                for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                    ny, nx_ = cy + dy, cx + dx
                    if (
                        0 <= ny < h
                        and 0 <= nx_ < w
                        and mask[ny, nx_]
                        and not labels[ny, nx_]
                    ):
                        labels[ny, nx_] = n
                        stack.append((ny, nx_))
    return labels, n


def detect_sunspots(
    data: np.ndarray,
    *,
    bright_percentile: float = 75.0,
    spot_frac: float = 0.85,
    min_pixels: int = 3,
) -> dict[str, Any]:
    """Deteccao esqueleto: disco circular a partir do brilho + manchas escuras."""
    arr = np.asarray(data, dtype=np.float64)
    if arr.ndim != 2:
        raise DomainError("imagem 2D requerida")
    finite = np.isfinite(arr)
    if not finite.any():
        raise DomainError("imagem sem pixels validos")
    thr = float(np.percentile(arr[finite], bright_percentile))
    bright = finite & (arr >= thr)
    if int(bright.sum()) < 10:
        thr = float(np.median(arr[finite]))
        bright = finite & (arr >= thr)
    ys, xs = np.where(bright)
    if ys.size == 0:
        return {"spots": 0, "groups": 0, "disk_pixels": 0, "centroids": []}
    cy = float(ys.mean())
    cx = float(xs.mean())
    radius = float(np.hypot(xs - cx, ys - cy).max()) * 1.05
    yy, xx = np.mgrid[0 : arr.shape[0], 0 : arr.shape[1]]
    disk = finite & (((xx - cx) ** 2 + (yy - cy) ** 2) <= radius**2)
    disk_vals = arr[disk]
    if disk_vals.size == 0:
        return {"spots": 0, "groups": 0, "disk_pixels": 0, "centroids": []}
    disk_med = float(np.median(disk_vals))
    spots_mask = disk & (arr < disk_med * float(spot_frac))
    labels, n_raw = _label_components(spots_mask)
    centroids: list[list[float]] = []
    kept = 0
    for lab in range(1, n_raw + 1):
        yx = np.where(labels == lab)
        if yx[0].size < min_pixels:
            continue
        kept += 1
        centroids.append([float(yx[1].mean()), float(yx[0].mean())])
    return {
        "spots": kept,
        "groups": kept,
        "disk_pixels": int(disk.sum()),
        "disk_median": disk_med,
        "centroids": centroids,
    }


class CountSunspots:
    """Produto solar_sunspots: checklist + contagem Wolf + pontos."""

    def __init__(self, archive: Any, store: LocalArtifactStore) -> None:
        self.archive = archive
        self.store = store

    def execute(
        self,
        *,
        workspace_id: UUID,
        fits_uri: str,
        filter_confirmed: bool,
        no_unfiltered_eyepiece: bool,
        daytime_acknowledged: bool,
        filter_name: str = "white-light",
        observer: str = "AstroCitizen",
        k: float = 1.0,
        spots: int | None = None,
        groups: int | None = None,
        program_id: UUID | None = None,
        observation_id: UUID | None = None,
        t_utc: str | None = None,
    ) -> AnalysisProduct:
        safety = validate_solar_safety(
            filter_confirmed=filter_confirmed,
            no_unfiltered_eyepiece=no_unfiltered_eyepiece,
            daytime_acknowledged=daytime_acknowledged,
            filter_name=filter_name,
        )
        path = self.store.resolve(fits_uri)
        with fits.open(path) as hdul:
            data = np.asarray(hdul[0].data, dtype=np.float64)
            hdr = hdul[0].header
        det = detect_sunspots(data)
        n_spots = int(spots) if spots is not None else int(det["spots"])
        n_groups = int(groups) if groups is not None else int(det["groups"])
        r_wolf = wolf_number(groups=n_groups, spots=n_spots, k=k)
        when = t_utc or hdr.get("DATE-OBS") or utc_now_iso()

        product = AnalysisProduct(
            id=new_id(),
            workspace_id=workspace_id,
            program_id=program_id,
            product_type="solar_sunspots",
            version_num=1,
            is_publishable=False,
            parameters={
                "method": "disk_threshold" if spots is None else "manual",
                "fits_uri": fits_uri,
                "filter_name": filter_name,
                "observer": observer,
                "k": k,
                "safety": safety,
                "detection": {
                    "disk_pixels": det["disk_pixels"],
                    "auto_spots": det["spots"],
                    "auto_groups": det["groups"],
                },
            },
            summary={
                "spots": n_spots,
                "groups": n_groups,
                "wolf_r": r_wolf,
                "epoch_utc": when,
                "filter_name": filter_name,
                "safety_ok": True,
            },
            state="ready",
        )
        product = self.archive.save_analysis_product(product)
        if observation_id:
            self.archive.link_product_observation(product.id, observation_id)
        points = []
        for i, (px, py) in enumerate(det.get("centroids") or []):
            points.append(
                {
                    "t_utc": when,
                    "sequence_index": i,
                    "x": float(px),
                    "y": float(py),
                    "y_err": None,
                    "band": "solar",
                    "meta": {"kind": "sunspot"},
                }
            )
        if not points:
            points.append(
                {
                    "t_utc": when,
                    "sequence_index": 0,
                    "x": float(n_groups),
                    "y": float(n_spots),
                    "y_err": None,
                    "band": "solar",
                    "meta": {"wolf_r": r_wolf},
                }
            )
        self.archive.save_measurement_points(product.id, points)
        return product

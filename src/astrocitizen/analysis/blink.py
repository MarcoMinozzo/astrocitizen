"""Blink / diff imaging (esqueleto PO-C03 / inicio AC-113)."""

from __future__ import annotations

from typing import Any
from uuid import UUID

import numpy as np
from astropy.io import fits

from astrocitizen.adapters.fs import LocalArtifactStore
from astrocitizen.analysis.astrometry import pixel_to_radec_tangent, pixel_to_radec_wcs
from astrocitizen.analysis.photometry import centroid
from astrocitizen.reduction.models import AnalysisProduct
from astrocitizen.shared.errors import DomainError
from astrocitizen.shared.ids import new_id
from astrocitizen.shared.timeutil import utc_now_iso


def find_peak(diff: np.ndarray, *, edge: int = 2) -> tuple[int, int, float]:
    """Pico absoluto no residual, ignorando borda."""
    arr = np.asarray(diff, dtype=np.float64)
    if arr.ndim != 2:
        raise DomainError("imagens 2D requeridas")
    work = np.abs(arr)
    e = max(int(edge), 0)
    if e > 0:
        work[:e, :] = 0
        work[-e:, :] = 0
        work[:, :e] = 0
        work[:, -e:] = 0
    y, x = np.unravel_index(int(np.argmax(work)), work.shape)
    return int(x), int(y), float(work[y, x])


def residual_snr(diff: np.ndarray, peak: float) -> float:
    med = float(np.median(diff))
    mad = float(np.median(np.abs(diff - med)))
    noise = 1.4826 * mad if mad > 0 else float(np.std(diff)) or 1.0
    return float(peak / noise)


class BlinkDiff:
    """Produto blink_candidate: new - ref, pico residual."""

    def __init__(self, archive: Any, store: LocalArtifactStore) -> None:
        self.archive = archive
        self.store = store

    def execute(
        self,
        *,
        workspace_id: UUID,
        new_uri: str,
        ref_uri: str,
        ra0_deg: float | None = None,
        dec0_deg: float | None = None,
        scale_arcsec: float | None = None,
        pa_deg: float = 0.0,
        program_id: UUID | None = None,
        observation_id: UUID | None = None,
        internal_name: str | None = None,
        edge: int = 2,
    ) -> AnalysisProduct:
        new_path = self.store.resolve(new_uri)
        ref_path = self.store.resolve(ref_uri)
        with fits.open(new_path) as hdul_n, fits.open(ref_path) as hdul_r:
            data_n = np.asarray(hdul_n[0].data, dtype=np.float64)
            data_r = np.asarray(hdul_r[0].data, dtype=np.float64)
            hdr = hdul_n[0].header
        if data_n.shape != data_r.shape:
            raise DomainError("new e ref com shapes diferentes")
        diff = data_n - data_r
        px, py, peak = find_peak(diff, edge=edge)
        cx, cy = centroid(np.abs(diff), float(px), float(py))
        snr = residual_snr(diff, peak)

        ra_dec = pixel_to_radec_wcs(hdr, cx, cy)
        if ra_dec is None and ra0_deg is not None and dec0_deg is not None and scale_arcsec:
            h, w = diff.shape
            ra_dec = pixel_to_radec_tangent(
                cx,
                cy,
                ra0_deg=ra0_deg,
                dec0_deg=dec0_deg,
                crpix1=(w - 1) / 2.0,
                crpix2=(h - 1) / 2.0,
                scale_arcsec=scale_arcsec,
                pa_deg=pa_deg,
            )
        ra_deg = ra_dec[0] if ra_dec else None
        dec_deg = ra_dec[1] if ra_dec else None

        out_key = f"analysis/blink/{new_id()}.fits"
        out_path = self.store.root / out_key
        out_path.parent.mkdir(parents=True, exist_ok=True)
        hdu = fits.PrimaryHDU(data=diff.astype(np.float32))
        hdu.header["DATE-OBS"] = hdr.get("DATE-OBS") or utc_now_iso()
        hdu.header["ORIGIN"] = "AstroCitizen/0.0.1"
        hdu.header["COMMENT"] = "blink residual = new - ref"
        hdu.writeto(out_path, overwrite=True)
        diff_uri = out_path.as_uri()
        when = hdr.get("DATE-OBS") or utc_now_iso()
        name = internal_name or hdr.get("OBJECT") or "SN-CAND"

        product = AnalysisProduct(
            id=new_id(),
            workspace_id=workspace_id,
            program_id=program_id,
            product_type="blink_candidate",
            version_num=1,
            is_publishable=False,
            parameters={
                "method": "frame_diff",
                "new_uri": new_uri,
                "ref_uri": ref_uri,
                "diff_uri": diff_uri,
                "peak_xy": [px, py],
                "centroid": [cx, cy],
                "internal_name": name,
            },
            summary={
                "peak": peak,
                "snr": snr,
                "ra_deg": ra_deg,
                "dec_deg": dec_deg,
                "epoch_utc": when,
            },
            state="ready",
        )
        product = self.archive.save_analysis_product(product)
        if observation_id:
            self.archive.link_product_observation(product.id, observation_id)
        self.archive.save_measurement_points(
            product.id,
            [
                {
                    "t_utc": when,
                    "sequence_index": 0,
                    "x": float(cx),
                    "y": float(cy),
                    "y_err": None,
                    "band": "diff",
                    "meta": {
                        "peak": peak,
                        "snr": snr,
                        "ra_deg": ra_deg,
                        "dec_deg": dec_deg,
                        "internal_name": name,
                    },
                }
            ],
        )
        return product

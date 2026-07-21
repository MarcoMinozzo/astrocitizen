"""Estatisticas / stretch de FITS para viewer CLI e GUI (AC-062)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
from astropy.io import fits


def fits_stats(path: Path) -> dict[str, Any]:
    with fits.open(path) as hdul:
        data = np.asarray(hdul[0].data, dtype=np.float64)
        hdr = dict(hdul[0].header)
    flat = data[np.isfinite(data)]
    if flat.size == 0:
        raise ValueError("imagem vazia")
    p1, p50, p99 = np.percentile(flat, [1, 50, 99])
    return {
        "shape": list(data.shape),
        "min": float(flat.min()),
        "max": float(flat.max()),
        "mean": float(flat.mean()),
        "median": float(p50),
        "std": float(flat.std()),
        "p1": float(p1),
        "p99": float(p99),
        "header_keys": sorted(list(hdr.keys()))[:40],
        "object": hdr.get("OBJECT"),
        "exptime": hdr.get("EXPTIME"),
    }


def stretch_display(data: np.ndarray, lo_pct: float = 1.0, hi_pct: float = 99.0) -> np.ndarray:
    """Normaliza para 0..255 uint8 (viewer)."""
    flat = data[np.isfinite(data)]
    lo, hi = np.percentile(flat, [lo_pct, hi_pct])
    if hi <= lo:
        hi = lo + 1.0
    scaled = (np.clip(data, lo, hi) - lo) / (hi - lo)
    return (scaled * 255.0).astype(np.uint8)

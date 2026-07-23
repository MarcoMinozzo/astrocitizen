"""Calibracao de comprimento de onda (AC-101).

Suporta:
- pares pix:nm (polinomio grau 1-3)
- deteccao de picos + catalogo Neon (seed linear)
- aplicacao a FITS 1D / produto spectrum_1d
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from uuid import UUID

import numpy as np
from astropy.io import fits

from astrocitizen.adapters.fs import LocalArtifactStore
from astrocitizen.reduction.models import AnalysisProduct
from astrocitizen.shared.errors import DomainError
from astrocitizen.shared.ids import new_id
from astrocitizen.shared.timeutil import utc_now_iso

# Linhas Neon tipicas (nm, ar) para espectrografos amadores R~500-2000.
NEON_LINES_NM: tuple[float, ...] = (
    585.249,
    588.189,
    594.483,
    597.553,
    603.000,
    607.434,
    609.616,
    614.306,
    616.359,
    621.728,
    626.649,
    630.479,
    633.443,
    638.299,
    640.225,
    650.653,
    653.288,
    659.895,
    667.828,
    671.704,
    692.947,
    703.241,
)

# Subconjunto Hg (nm) util em labs.
HG_LINES_NM: tuple[float, ...] = (
    404.656,
    435.833,
    546.074,
    576.960,
    579.066,
)

CATALOGS: dict[str, tuple[float, ...]] = {
    "neon": NEON_LINES_NM,
    "ne": NEON_LINES_NM,
    "hg": HG_LINES_NM,
    "mercury": HG_LINES_NM,
}


@dataclass(slots=True)
class WavelengthSolution:
    coeffs: list[float]  # wave = sum coeffs[k] * pix**k  (pix 0-based)
    degree: int
    rms_nm: float
    n_anchors: int
    method: str
    anchors: list[tuple[float, float]] = field(default_factory=list)  # (pix, nm)
    unit: str = "nm"

    def wave_at(self, pix: np.ndarray | float) -> np.ndarray | float:
        x = np.asarray(pix, dtype=float)
        y = np.zeros_like(x, dtype=float)
        for k, c in enumerate(self.coeffs):
            y = y + float(c) * (x**k)
        if np.isscalar(pix):
            return float(y)
        return y

    def wave_array(self, n_pix: int) -> np.ndarray:
        return np.asarray(self.wave_at(np.arange(n_pix, dtype=float)), dtype=float)

    def to_header_cards(self) -> dict[str, Any]:
        cards: dict[str, Any] = {
            "AC_WDEG": int(self.degree),
            "AC_WRMS": float(self.rms_nm),
            "AC_WNANC": int(self.n_anchors),
            "AC_WMETH": str(self.method)[:68],
            "CUNIT1": self.unit,
            "CTYPE1": "WAVE",
        }
        for k, c in enumerate(self.coeffs):
            cards[f"AC_WC{k}"] = float(c)
        return cards


def parse_wave_pairs(text: str) -> list[tuple[float, float]]:
    """Parse 'pix:nm,pix:nm,...' (nm)."""
    pairs: list[tuple[float, float]] = []
    raw = (text or "").strip()
    if not raw:
        raise DomainError("wave-pairs vazio")
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        if ":" not in part:
            raise DomainError(f"par invalido (use pix:nm): {part}")
        a, b = part.split(":", 1)
        pairs.append((float(a.strip()), float(b.strip())))
    if len(pairs) < 2:
        raise DomainError("precisa de pelo menos 2 pares pix:nm")
    return pairs


def fit_wavelength_poly(
    pixels: np.ndarray | list[float],
    waves_nm: np.ndarray | list[float],
    *,
    degree: int | None = None,
    method: str = "pairs",
) -> WavelengthSolution:
    """Ajuste polinomial pix → nm (grau automatico se None)."""
    x = np.asarray(pixels, dtype=float)
    y = np.asarray(waves_nm, dtype=float)
    if x.size != y.size or x.size < 2:
        raise DomainError("anchors insuficientes para calibracao")
    if degree is None:
        degree = min(2, x.size - 1)
    degree = int(degree)
    if degree < 1 or degree > 3:
        raise DomainError("degree deve ser 1..3")
    if x.size < degree + 1:
        raise DomainError(f"precisa de >= {degree + 1} anchors para grau {degree}")
    coeffs = np.polyfit(x, y, degree)
    # np.polyfit: highest power first → reverse to c0..cn
    c_low = [float(v) for v in coeffs[::-1]]
    pred = np.zeros_like(x)
    for k, c in enumerate(c_low):
        pred = pred + c * (x**k)
    rms = float(np.sqrt(np.mean((pred - y) ** 2)))
    anchors = [(float(px), float(wy)) for px, wy in zip(x, y, strict=True)]
    return WavelengthSolution(
        coeffs=c_low,
        degree=degree,
        rms_nm=rms,
        n_anchors=len(anchors),
        method=method,
        anchors=anchors,
    )


def wavelength_linear(
    n_pix: int,
    *,
    wave0_nm: float | None = None,
    wave1_nm: float | None = None,
    pix_a: float | None = None,
    wave_a_nm: float | None = None,
    pix_b: float | None = None,
    wave_b_nm: float | None = None,
) -> np.ndarray:
    """Solucao linear (2 pontos ou extremos)."""
    if n_pix < 2:
        raise DomainError("espectro demasiado curto")
    if wave0_nm is not None and wave1_nm is not None:
        return np.linspace(float(wave0_nm), float(wave1_nm), n_pix)
    if None not in (pix_a, wave_a_nm, pix_b, wave_b_nm):
        sol = fit_wavelength_poly(
            [float(pix_a), float(pix_b)],
            [float(wave_a_nm), float(wave_b_nm)],
            degree=1,
            method="linear_two_point",
        )
        return sol.wave_array(n_pix)
    return np.arange(n_pix, dtype=float)


def detect_emission_peaks(
    flux: np.ndarray,
    *,
    max_peaks: int = 25,
    min_separation: int = 3,
    prominence_frac: float = 0.05,
) -> list[float]:
    """Picos de emissao (centroide local) em pix 0-based."""
    arr = np.asarray(flux, dtype=float)
    if arr.ndim != 1 or arr.size < 8:
        raise DomainError("fluxo 1D curto demais para picos")
    med = float(np.nanmedian(arr))
    mad = float(np.nanmedian(np.abs(arr - med))) * 1.4826
    floor = med + max(mad * 5.0, (np.nanmax(arr) - med) * prominence_frac)
    # candidatos: maximos locais acima do floor
    cand: list[int] = []
    for i in range(1, len(arr) - 1):
        if arr[i] >= arr[i - 1] and arr[i] >= arr[i + 1] and arr[i] >= floor:
            cand.append(i)
    # ordenar por intensidade
    cand.sort(key=lambda i: float(arr[i]), reverse=True)
    picked: list[int] = []
    for i in cand:
        if any(abs(i - j) < min_separation for j in picked):
            continue
        picked.append(i)
        if len(picked) >= max_peaks:
            break
    # centroide ±2
    peaks: list[float] = []
    for i in sorted(picked):
        lo, hi = max(0, i - 2), min(len(arr), i + 3)
        seg = arr[lo:hi]
        w = np.clip(seg - med, 0, None)
        xs = np.arange(lo, hi, dtype=float)
        if float(np.sum(w)) <= 0:
            peaks.append(float(i))
        else:
            peaks.append(float(np.sum(xs * w) / np.sum(w)))
    return peaks


def match_peaks_to_catalog(
    peaks_pix: list[float],
    catalog_nm: tuple[float, ...] | list[float],
    *,
    wave0_nm: float,
    wave1_nm: float,
    n_pix: int,
    max_residual_nm: float = 2.5,
) -> list[tuple[float, float]]:
    """Casa picos com linhas do catalogo usando seed linear wave0..wave1."""
    if n_pix < 2:
        raise DomainError("n_pix invalido")
    scale = (float(wave1_nm) - float(wave0_nm)) / float(n_pix - 1)
    pred = [float(wave0_nm) + p * scale for p in peaks_pix]
    used_lines: set[int] = set()
    pairs: list[tuple[float, float]] = []
    order = sorted(range(len(peaks_pix)), key=lambda i: -abs(pred[i]))
    # match greedily by closest unused catalog line
    for i in sorted(range(len(peaks_pix)), key=lambda j: peaks_pix[j]):
        _ = order
        best_j = None
        best_d = max_residual_nm
        for j, line in enumerate(catalog_nm):
            if j in used_lines:
                continue
            d = abs(pred[i] - float(line))
            if d < best_d:
                best_d = d
                best_j = j
        if best_j is not None:
            used_lines.add(best_j)
            pairs.append((float(peaks_pix[i]), float(catalog_nm[best_j])))
    if len(pairs) < 2:
        raise DomainError(
            "poucos matches lamp→catalogo; ajuste --wave0/--wave1 seed ou catalogo"
        )
    return pairs


def solution_from_header(hdr: Any) -> WavelengthSolution | None:
    if hdr.get("AC_WDEG") is None:
        return None
    degree = int(hdr["AC_WDEG"])
    coeffs = []
    for k in range(degree + 1):
        key = f"AC_WC{k}"
        if key not in hdr:
            raise DomainError(f"header incompleto: falta {key}")
        coeffs.append(float(hdr[key]))
    anchors: list[tuple[float, float]] = []
    return WavelengthSolution(
        coeffs=coeffs,
        degree=degree,
        rms_nm=float(hdr.get("AC_WRMS") or 0.0),
        n_anchors=int(hdr.get("AC_WNANC") or 0),
        method=str(hdr.get("AC_WMETH") or "header"),
        anchors=anchors,
        unit=str(hdr.get("CUNIT1") or "nm"),
    )


def write_calibrated_spectrum(
    flux: np.ndarray,
    solution: WavelengthSolution,
    out_path: Path,
    *,
    meta_header: dict[str, Any] | None = None,
) -> np.ndarray:
    """Escreve FITS 1D com solucao polinomial nos headers (+ CRVAL/CDELT approx)."""
    flux = np.asarray(flux, dtype=np.float32)
    wave = solution.wave_array(len(flux))
    hdu = fits.PrimaryHDU(data=flux)
    hdr = hdu.header
    if meta_header:
        for k, v in meta_header.items():
            if v is None:
                continue
            try:
                hdr[k] = v
            except (ValueError, TypeError):
                hdr[k] = str(v)[:68]
    for k, v in solution.to_header_cards().items():
        hdr[k] = v
    # aproximacao linear para leitores simples
    hdr["CRVAL1"] = float(wave[0])
    hdr["CDELT1"] = float(wave[1] - wave[0]) if len(wave) > 1 else 1.0
    hdr["CRPIX1"] = 1.0
    hdr["ORIGIN"] = "AstroCitizen/0.0.1"
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    hdu.writeto(out_path, overwrite=True)
    return wave


def load_flux_1d(path: Path) -> tuple[np.ndarray, fits.Header]:
    path = Path(path)
    if not path.is_file():
        raise DomainError(f"FITS nao encontrado: {path}")
    with fits.open(path) as hdul:
        data = np.asarray(hdul[0].data, dtype=np.float64)
        hdr = hdul[0].header.copy()
    if data.ndim != 1:
        raise DomainError("calibracao λ requer espectro 1D")
    return data, hdr


class CalibrateWavelength:
    """Aplica solucao λ a um spectrum_1d (ou FITS 1D) → novo produto."""

    def __init__(self, archive: Any, store: LocalArtifactStore) -> None:
        self.archive = archive
        self.store = store

    def execute(
        self,
        *,
        workspace_id: UUID,
        fits_uri: str | None = None,
        product_id: UUID | None = None,
        wave_pairs: str | None = None,
        degree: int | None = None,
        lamp_uri: str | None = None,
        catalog: str = "neon",
        wave0_nm: float | None = None,
        wave1_nm: float | None = None,
        program_id: UUID | None = None,
    ) -> AnalysisProduct:
        src_uri, flux, hdr, parent_id = self._resolve_input(
            fits_uri=fits_uri, product_id=product_id
        )
        n = len(flux)
        if wave_pairs:
            pairs = parse_wave_pairs(wave_pairs)
            sol = fit_wavelength_poly(
                [p for p, _ in pairs],
                [w for _, w in pairs],
                degree=degree,
                method="pairs",
            )
        elif lamp_uri:
            if wave0_nm is None or wave1_nm is None:
                raise DomainError("lamp matching requer --wave0 e --wave1 (seed)")
            cat_name = catalog.strip().lower()
            if cat_name not in CATALOGS:
                raise DomainError(f"catalogo desconhecido: {catalog}")
            lamp_path = self.store.resolve(lamp_uri)
            lamp_flux, _ = load_flux_1d(lamp_path)
            if len(lamp_flux) != n:
                # allow different length: match in lamp pix space then user must
                # use same extraction geometry — require equal for MVP
                raise DomainError(
                    "lamp e ciencia devem ter o mesmo n_pix (mesma extracao)"
                )
            peaks = detect_emission_peaks(lamp_flux)
            pairs = match_peaks_to_catalog(
                peaks,
                CATALOGS[cat_name],
                wave0_nm=float(wave0_nm),
                wave1_nm=float(wave1_nm),
                n_pix=n,
            )
            sol = fit_wavelength_poly(
                [p for p, _ in pairs],
                [w for _, w in pairs],
                degree=degree if degree is not None else min(2, len(pairs) - 1),
                method=f"lamp:{cat_name}",
            )
        else:
            raise DomainError("indique --wave-pairs ou --lamp-uri")

        out_key = f"analysis/spectrum/{new_id()}_wcal.fits"
        out_path = self.store.root / out_key
        meta = {
            "OBJECT": hdr.get("OBJECT") or hdr.get("OBJNAME") or "SPEC",
            "DATE-OBS": hdr.get("DATE-OBS") or utc_now_iso(),
            "ACMETHOD": "wavelength_calib_v1",
        }
        wave = write_calibrated_spectrum(flux, sol, out_path, meta_header=meta)
        uri = out_path.as_uri()
        step = max(1, len(wave) // 64)
        when = str(meta["DATE-OBS"])
        points = [
            {
                "t_utc": when,
                "sequence_index": i,
                "x": float(wave[i]),
                "y": float(flux[i]),
                "y_err": None,
                "band": "spec",
                "meta": {"unit_x": "nm", "wavelength_solution": True},
            }
            for i in range(0, len(wave), step)
        ]
        product = AnalysisProduct(
            id=new_id(),
            workspace_id=workspace_id,
            program_id=program_id,
            product_type="spectrum_1d",
            version_num=1,
            is_publishable=False,
            parameters={
                "method": "wavelength_calib_v1",
                "source_uri": src_uri,
                "parent_product_id": str(parent_id) if parent_id else None,
                "spectrum_uri": uri,
                "wavelength_calibrated": True,
                "wavelength_degree": sol.degree,
                "wavelength_rms_nm": sol.rms_nm,
                "wavelength_method": sol.method,
                "wavelength_coeffs": sol.coeffs,
                "n_anchors": sol.n_anchors,
                "anchors": [{"pix": a, "nm": b} for a, b in sol.anchors],
                "n_pix": n,
                "wave0_nm": float(wave[0]),
                "wave1_nm": float(wave[-1]),
            },
            summary={
                "wave0_nm": float(wave[0]),
                "wave1_nm": float(wave[-1]),
                "rms_nm": sol.rms_nm,
                "degree": sol.degree,
                "n_anchors": sol.n_anchors,
                "method": sol.method,
                "n_points": len(points),
            },
            state="ready",
        )
        product = self.archive.save_analysis_product(product)
        self.archive.save_measurement_points(product.id, points)
        return product

    def _resolve_input(
        self,
        *,
        fits_uri: str | None,
        product_id: UUID | None,
    ) -> tuple[str, np.ndarray, fits.Header, UUID | None]:
        if product_id is not None:
            product = self.archive.get_analysis_product(product_id)
            if product is None:
                raise DomainError(f"produto nao encontrado: {product_id}")
            uri = product.parameters.get("spectrum_uri") or product.parameters.get(
                "fits_uri"
            )
            if not uri:
                raise DomainError("produto sem spectrum_uri")
            flux, hdr = load_flux_1d(self.store.resolve(str(uri)))
            return str(uri), flux, hdr, product.id
        if fits_uri:
            flux, hdr = load_flux_1d(self.store.resolve(fits_uri))
            return fits_uri, flux, hdr, None
        raise DomainError("indique --fits-uri ou --product")

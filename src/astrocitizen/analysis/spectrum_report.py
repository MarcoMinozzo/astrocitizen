"""Interpretacao espectral assistida (PO-B01/B03 / ARAS-style).

Gera um relatorio estruturado: linhas candidatas, telurico, pista de classe,
e comparacao multi-epoca (como analise cidadã de SN/eruptivas).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
from uuid import UUID

import numpy as np
from astropy.io import fits

from astrocitizen.adapters.fs import LocalArtifactStore
from astrocitizen.reduction.models import AnalysisProduct
from astrocitizen.shared.errors import DomainError
from astrocitizen.shared.ids import new_id

# Rest wavelengths in Angstrom (vacuum/air approx for citizen R~500-2000).
LINE_CATALOG: list[dict[str, Any]] = [
    {"name": "H-delta", "wave_A": 4101.7, "kind": "balmer", "role": "SN/stellar"},
    {"name": "H-gamma", "wave_A": 4340.5, "kind": "balmer", "role": "SN/stellar"},
    {"name": "H-beta", "wave_A": 4861.3, "kind": "balmer", "role": "SN/stellar"},
    {"name": "He I 5876", "wave_A": 5875.6, "kind": "he", "role": "SN/Be"},
    {"name": "Na D", "wave_A": 5892.9, "kind": "metal", "role": "ISM/stellar"},
    {"name": "Si II 6355", "wave_A": 6355.0, "kind": "si", "role": "SN Ia marker"},
    {"name": "H-alpha", "wave_A": 6562.8, "kind": "balmer", "role": "SN II / Be / stellar"},
    {"name": "O2 A (telluric)", "wave_A": 7605.0, "kind": "telluric", "role": "atmosphere"},
    {"name": "Ca II 8542", "wave_A": 8542.1, "kind": "ca", "role": "stellar/SN"},
]


def load_spectrum_arrays(
    path: Path,
) -> tuple[np.ndarray, np.ndarray, dict[str, Any]]:
    """Load 1D FITS -> wavelength Angstrom, flux, meta."""
    path = Path(path)
    if not path.is_file():
        raise DomainError(f"FITS nao encontrado: {path}")
    with fits.open(path) as hdul:
        data = np.asarray(hdul[0].data, dtype=np.float64)
        hdr = hdul[0].header
    if data.ndim != 1:
        raise DomainError("espectro_report requer FITS 1D")
    n = len(data)
    # AC-101: solucao polinomial pix→nm nos headers
    if hdr.get("AC_WDEG") is not None:
        from astrocitizen.analysis.wavelength_calib import solution_from_header

        sol = solution_from_header(hdr)
        assert sol is not None
        wave_nm = sol.wave_array(n)
        wave = wave_nm * 10.0  # nm → Angstrom
        unit = "Angstrom"
    else:
        crval = float(hdr.get("CRVAL1", 1.0))
        cdelt = float(hdr.get("CDELT1", 1.0))
        crpix = float(hdr.get("CRPIX1", 1.0))
        wave = crval + (np.arange(n, dtype=float) + 1.0 - crpix) * cdelt
        unit = str(hdr.get("CUNIT1") or "").lower()
        ctype = str(hdr.get("CTYPE1") or "").upper()
        # nm -> Angstrom
        if "nm" in unit or (cdelt < 2.0 and crval < 2000 and "ANG" not in ctype):
            if 200.0 < crval < 2000.0 and "ang" not in unit:
                wave = wave * 10.0
                unit = "Angstrom"
    meta = {
        "object": hdr.get("OBJECT") or hdr.get("OBJNAME") or hdr.get("BSS_OBJ") or "",
        "date_obs": hdr.get("DATE-OBS") or "",
        "instrument": hdr.get("INSTRUME") or hdr.get("BSS_INST") or "",
        "observer": hdr.get("OBSERVER") or "",
        "cunit1": unit or "Angstrom",
        "n_pix": n,
        "wave0_A": float(wave[0]),
        "wave1_A": float(wave[-1]),
    }
    return wave, data, meta


def _window_indices(wave: np.ndarray, center: float, half_width: float) -> np.ndarray:
    return np.where((wave >= center - half_width) & (wave <= center + half_width))[0]


def detect_line_features(
    wave: np.ndarray,
    flux: np.ndarray,
    *,
    half_width_A: float = 40.0,
    snr_min: float = 3.0,
) -> list[dict[str, Any]]:
    """Procura extrema locais perto do catalogo (emissao/absorcao)."""
    wave = np.asarray(wave, dtype=float)
    flux = np.asarray(flux, dtype=float)
    if len(wave) < 10:
        raise DomainError("espectro demasiado curto")
    global_med = float(np.median(flux))
    global_noise = float(np.median(np.abs(flux - global_med))) * 1.4826 or 1.0
    found: list[dict[str, Any]] = []
    for line in LINE_CATALOG:
        idx = _window_indices(wave, float(line["wave_A"]), half_width_A)
        if idx.size < 5:
            continue
        seg = flux[idx]
        wseg = wave[idx]
        # local continuum: median of outer thirds of the window
        n = len(seg)
        edge = max(2, n // 3)
        local = np.concatenate([seg[:edge], seg[-edge:]])
        continuum = float(np.median(local))
        noise = float(np.median(np.abs(local - continuum))) * 1.4826 or global_noise
        i_max = int(np.argmax(seg))
        i_min = int(np.argmin(seg))
        peak = float(seg[i_max])
        trough = float(seg[i_min])
        em_snr = (peak - continuum) / noise
        ab_snr = (continuum - trough) / noise
        if em_snr >= snr_min and em_snr >= ab_snr:
            found.append(
                {
                    "name": line["name"],
                    "rest_A": line["wave_A"],
                    "kind": line["kind"],
                    "role": line["role"],
                    "feature": "emission",
                    "obs_A": float(wseg[i_max]),
                    "strength": float(em_snr),
                    "delta_A": float(wseg[i_max] - line["wave_A"]),
                }
            )
        elif ab_snr >= snr_min:
            found.append(
                {
                    "name": line["name"],
                    "rest_A": line["wave_A"],
                    "kind": line["kind"],
                    "role": line["role"],
                    "feature": "absorption",
                    "obs_A": float(wseg[i_min]),
                    "strength": float(ab_snr),
                    "delta_A": float(wseg[i_min] - line["wave_A"]),
                }
            )
    found.sort(key=lambda x: -x["strength"])
    return found


def classify_hint(features: list[dict[str, Any]]) -> dict[str, Any]:
    """Pista grosseira (nao substitui classificacao humana/template)."""
    by = {f["name"]: f for f in features}
    balmer_em = [
        n
        for n in ("H-alpha", "H-beta", "H-gamma", "H-delta")
        if n in by and by[n]["feature"] == "emission"
    ]
    si = by.get("Si II 6355")
    notes: list[str] = []
    label = "undetermined"
    confidence = "low"
    if balmer_em and (si is None or si["feature"] != "absorption" or si["strength"] < 3):
        label = "H-rich (SN II-like / Be / emission-line)"
        confidence = "medium" if "H-alpha" in balmer_em else "low"
        notes.append("Balmer emission detected; consistent with H-rich transient or Be star.")
    if si and si["feature"] == "absorption" and si["strength"] >= 3:
        label = "Si II absorption present (SN Ia-like candidate)"
        confidence = "low"
        notes.append("Si II 6355 absorption is a classic SN Ia marker; confirm with templates.")
    if "O2 A (telluric)" in by:
        notes.append("Telluric O2 A-band near 7605 A is atmospheric, not astrophysical.")
    if not notes:
        notes.append("No strong catalog matches; check wavelength solution and SNR.")
    return {"label": label, "confidence": confidence, "notes": notes, "balmer_emission": balmer_em}


def continuum_blue_red_ratio(wave: np.ndarray, flux: np.ndarray) -> dict[str, float]:
    """Razao continua azul/vermelho para evolucao multi-epoca."""
    blue = flux[(wave >= 4000) & (wave <= 5000)]
    red = flux[(wave >= 6500) & (wave <= 7500)]
    b = float(np.median(blue)) if blue.size else float("nan")
    r = float(np.median(red)) if red.size else float("nan")
    ratio = b / r if r and np.isfinite(r) and r != 0 else float("nan")
    return {"blue_med": b, "red_med": r, "blue_red_ratio": ratio}


def format_spectrum_report(
    *,
    meta: dict[str, Any],
    features: list[dict[str, Any]],
    hint: dict[str, Any],
    continuum: dict[str, float],
    epochs: list[dict[str, Any]] | None = None,
) -> str:
    """Texto legivel (estilo analise ARAS/citizen)."""
    lines = [
        "#TYPE=ASTROCITIZEN_SPECTRUM_REPORT",
        f"#OBJECT={meta.get('object') or '-'}",
        f"#DATE-OBS={meta.get('date_obs') or '-'}",
        f"#INSTRUME={meta.get('instrument') or '-'}",
        f"#OBSERVER={meta.get('observer') or '-'}",
        f"#WAVE={meta.get('wave0_A'):.1f}-{meta.get('wave1_A'):.1f} A",
        f"#NPIX={meta.get('n_pix')}",
        "#",
        f"#CLASS_HINT={hint.get('label')}",
        f"#CONFIDENCE={hint.get('confidence')}",
        f"#BLUE_RED_RATIO={continuum.get('blue_red_ratio')}",
        "#",
        "#FEATURES (name feature obs_A rest_A strength)",
    ]
    for f in features[:12]:
        lines.append(
            f"{f['name']}\t{f['feature']}\t{f['obs_A']:.1f}\t{f['rest_A']:.1f}\t{f['strength']:.1f}"
        )
    lines.append("#")
    lines.append("#NOTES")
    for n in hint.get("notes") or []:
        lines.append(f"# {n}")
    if epochs:
        lines.append("#")
        lines.append("#EPOCHS (date blue_red_ratio n_features)")
        for e in epochs:
            lines.append(
                f"{e.get('date_obs')}\t{e.get('blue_red_ratio')}\t{e.get('n_features')}"
            )
            if e.get("evolution_note"):
                lines.append(f"#  {e['evolution_note']}")
    return "\n".join(lines) + "\n"


def compare_epochs(epoch_summaries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Anota evolucao do ratio azul/vermelho entre epocas ordenadas."""
    ordered = sorted(epoch_summaries, key=lambda e: str(e.get("date_obs") or ""))
    out: list[dict[str, Any]] = []
    prev_r = None
    for e in ordered:
        r = e.get("blue_red_ratio")
        note = None
        if prev_r is not None and r is not None and np.isfinite(prev_r) and np.isfinite(r):
            dro = (r - prev_r) / prev_r if prev_r else 0.0
            if dro < -0.15:
                note = "Blue continuum relative drop vs previous epoch (>15%)."
            elif dro > 0.15:
                note = "Blue continuum relative rise vs previous epoch (>15%)."
        item = dict(e)
        item["evolution_note"] = note
        out.append(item)
        prev_r = r
    return out


class InterpretSpectrum:
    """Produto spectrum_report a partir de 1+ espectros 1D."""

    def __init__(self, archive: Any, store: LocalArtifactStore) -> None:
        self.archive = archive
        self.store = store

    def _resolve_spectrum_path(self, *, fits_uri: str | None, product_id: UUID | None) -> Path:
        if fits_uri:
            return self.store.resolve(fits_uri)
        if product_id is None:
            raise DomainError("passe --fits-uri ou --product")
        product = self.archive.get_analysis_product(product_id)
        if product is None:
            raise DomainError(f"produto nao encontrado: {product_id}")
        uri = product.parameters.get("spectrum_uri") or product.parameters.get("fits_uri")
        if not uri:
            raise DomainError("produto sem spectrum_uri/fits_uri")
        return self.store.resolve(str(uri))

    def execute(
        self,
        *,
        workspace_id: UUID,
        fits_uri: str | None = None,
        product_id: UUID | None = None,
        extra_product_ids: list[UUID] | None = None,
        program_id: UUID | None = None,
        half_width_A: float = 40.0,
        snr_min: float = 3.0,
        out_path: Path | None = None,
    ) -> AnalysisProduct:
        path = self._resolve_spectrum_path(fits_uri=fits_uri, product_id=product_id)
        wave, flux, meta = load_spectrum_arrays(path)
        features = detect_line_features(
            wave, flux, half_width_A=half_width_A, snr_min=snr_min
        )
        hint = classify_hint(features)
        continuum = continuum_blue_red_ratio(wave, flux)

        epoch_summaries = [
            {
                "date_obs": meta.get("date_obs"),
                "blue_red_ratio": continuum.get("blue_red_ratio"),
                "n_features": len(features),
                "source": str(path.name),
            }
        ]
        for pid in extra_product_ids or []:
            pth = self._resolve_spectrum_path(fits_uri=None, product_id=pid)
            w2, f2, m2 = load_spectrum_arrays(pth)
            feat2 = detect_line_features(w2, f2, half_width_A=half_width_A, snr_min=snr_min)
            cont2 = continuum_blue_red_ratio(w2, f2)
            epoch_summaries.append(
                {
                    "date_obs": m2.get("date_obs"),
                    "blue_red_ratio": cont2.get("blue_red_ratio"),
                    "n_features": len(feat2),
                    "source": str(pth.name),
                }
            )
        epochs = compare_epochs(epoch_summaries) if len(epoch_summaries) > 1 else None

        text = format_spectrum_report(
            meta=meta,
            features=features,
            hint=hint,
            continuum=continuum,
            epochs=epochs,
        )
        out_key = f"analysis/spectrum_report/{new_id()}.txt"
        out_path = Path(out_path) if out_path else (self.store.root / out_key)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(text, encoding="utf-8")
        try:
            report_uri = out_path.as_uri()
            # ensure under store root for resolve()
            out_path.relative_to(self.store.root)
        except ValueError:
            report_uri = self.store.put(out_path, key=out_key)
            out_path = self.store.resolve(report_uri)
        else:
            report_uri = out_path.as_uri()

        product = AnalysisProduct(
            id=new_id(),
            workspace_id=workspace_id,
            program_id=program_id,
            product_type="spectrum_report",
            version_num=1,
            is_publishable=False,
            parameters={
                "method": "catalog_window_extrema",
                "fits_uri": fits_uri,
                "source_product_id": str(product_id) if product_id else None,
                "extra_product_ids": [str(x) for x in (extra_product_ids or [])],
                "half_width_A": half_width_A,
                "snr_min": snr_min,
                "report_uri": report_uri,
                "report_path": str(out_path),
            },
            summary={
                "object": meta.get("object"),
                "date_obs": meta.get("date_obs"),
                "n_features": len(features),
                "class_hint": hint.get("label"),
                "confidence": hint.get("confidence"),
                "blue_red_ratio": continuum.get("blue_red_ratio"),
                "top_line": features[0]["name"] if features else None,
                "n_epochs": len(epoch_summaries),
            },
            state="ready",
        )
        product = self.archive.save_analysis_product(product)
        return product

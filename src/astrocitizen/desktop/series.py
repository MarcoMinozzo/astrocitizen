"""Series helpers for GUI plots (no Qt dependency)."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse
from urllib.request import url2pathname


# Preferencia: artefacto derivado / exportavel antes do FITS bruto.
ARTIFACT_PARAM_KEYS: tuple[str, ...] = (
    "wcs_uri",
    "spectrum_uri",
    "diff_uri",
    "uri",
    "report_uri",
    "report_path",
    "fits_uri",
    "source_uri",
    "new_uri",
    "ref_uri",
)


def primary_artifact_refs(product: Any) -> list[tuple[str, str]]:
    """Lista (label, uri_ou_path) a partir de parameters do produto."""
    params = getattr(product, "parameters", None) or {}
    if not isinstance(params, dict):
        return []
    out: list[tuple[str, str]] = []
    seen: set[str] = set()
    for key in ARTIFACT_PARAM_KEYS:
        val = params.get(key)
        if not val:
            continue
        text = str(val).strip()
        if not text or text in seen:
            continue
        seen.add(text)
        out.append((key, text))
    extras = params.get("source_uris")
    if isinstance(extras, (list, tuple)):
        for i, val in enumerate(extras):
            if not val:
                continue
            text = str(val).strip()
            if not text or text in seen:
                continue
            seen.add(text)
            out.append((f"source_uris[{i}]", text))
    return out


def resolve_openable_path(
    ref: str,
    *,
    store_root: Path | None = None,
) -> Path | None:
    """Resolve file:// / path para Path existente (ficheiro ou pasta).

    Tenta ArtifactStore se store_root for dado; senao path local / file URI.
    """
    text = (ref or "").strip()
    if not text:
        return None
    if store_root is not None:
        try:
            from astrocitizen.adapters.fs import LocalArtifactStore

            path = LocalArtifactStore(store_root).resolve(text)
            if path.is_file() or path.is_dir():
                return path
        except Exception:
            pass
    parsed = urlparse(text)
    if parsed.scheme == "file":
        path = Path(url2pathname(unquote(parsed.path)))
    elif parsed.scheme in ("",):
        path = Path(text)
    else:
        return None
    try:
        path = path.expanduser().resolve()
    except OSError:
        return None
    if path.is_file() or path.is_dir():
        return path
    return None


def export_networks_for_type(product_type: str) -> list[str]:
    """Redes com export directo razoavel a partir do tipo de produto."""
    t = (product_type or "").strip().lower()
    if t in ("light_curve", "photometry"):
        return ["aavso", "exoclock"]
    if t == "spectrum_1d":
        return ["bess"]
    if t == "solar_sunspots":
        return ["solar"]
    if t == "astrometry":
        return ["mpc"]
    if t == "blink_candidate":
        return ["tns"]
    return []


def cli_export_hint(product_id: str, product_type: str | None = None) -> str:
    """Texto de comandos CLI contribute (fallback)."""
    pid = product_id.strip()
    nets = export_networks_for_type(product_type or "")
    lines = ["Export / contribuicao via CLI (espelho da GUI):", ""]
    if "aavso" in nets or not nets:
        lines.append(
            f"  astrocitizen contribute aavso --product {pid} "
            "--star NAME --out ./aavso.txt"
        )
    if "exoclock" in nets or not nets:
        lines.append(
            f"  astrocitizen contribute exoclock --product {pid} --out ./exo.csv"
        )
    if "solar" in nets or not nets:
        lines.append(
            f"  astrocitizen contribute solar --product {pid} --out ./solar/"
        )
    if "bess" in nets:
        lines.append(
            f"  astrocitizen contribute bess --product {pid} --out ./bess.fits"
        )
    if "mpc" in nets:
        lines.append(
            f"  astrocitizen contribute mpc --product {pid} --out ./mpc.psv"
        )
    lines.append("")
    lines.append("Ajuste a rede e flags conforme o tipo; ou use Exportar na GUI.")
    return "\n".join(lines)


def series_from_measurement_points(
    points: list[dict[str, Any]],
) -> tuple[list[float], list[float], str]:
    """Extrai (xs, ys, label) de measurement_points.

    Preferencia: x/y numericos; senao sequence_index como x.
    label = band do primeiro ponto ou 'y'.
    """
    xs: list[float] = []
    ys: list[float] = []
    band = "y"
    for i, p in enumerate(points):
        y_raw = p.get("y")
        if y_raw is None:
            continue
        try:
            y = float(y_raw)
        except (TypeError, ValueError):
            continue
        x_raw = p.get("x")
        if x_raw is None:
            x_raw = p.get("sequence_index", i)
        try:
            x = float(x_raw)
        except (TypeError, ValueError):
            x = float(i)
        xs.append(x)
        ys.append(y)
        if p.get("band") and band == "y":
            band = str(p["band"])
    return xs, ys, band


def format_product_detail(product: Any, *, n_points: int = 0) -> str:
    """Texto legivel de detalhe do produto."""
    summary = getattr(product, "summary", None) or {}
    params = getattr(product, "parameters", None) or {}
    lines = [
        f"id={product.id}",
        f"type={product.product_type}",
        f"state={product.state}",
        f"points={n_points}",
    ]
    if summary:
        lines.append("summary:")
        for k, v in list(summary.items())[:12]:
            lines.append(f"  {k}: {v}")
    keys = (
        "channel",
        *ARTIFACT_PARAM_KEYS,
    )
    extras = {k: params[k] for k in keys if k in params and params[k]}
    if extras:
        lines.append("parameters:")
        for k, v in extras.items():
            lines.append(f"  {k}: {v}")
    return "\n".join(lines)

"""Series helpers for GUI plots (no Qt dependency)."""

from __future__ import annotations

from typing import Any


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
    keys = ("channel", "fits_uri", "spectrum_uri", "source_uri", "report_path")
    extras = {k: params[k] for k in keys if k in params and params[k]}
    if extras:
        lines.append("parameters:")
        for k, v in extras.items():
            lines.append(f"  {k}: {v}")
    return "\n".join(lines)

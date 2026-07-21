"""Pacote de reporte IOTA (PO-D01) - estilo IOTA-ES + meta."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def format_iota_es_txt(
    *,
    event_id: str,
    star: str,
    asteroid: str,
    observer: str,
    latitude_deg: float,
    longitude_deg: float,
    elevation_m: float,
    result: str,
    d_time_utc: str | None = None,
    r_time_utc: str | None = None,
    timesource: str = "NTP",
    instrument: str = "AstroCitizen",
    notes: str = "",
) -> str:
    """Formulario texto simplificado (inspirado IOTA-ES / Occult)."""
    lines = [
        "IOTA-ES_report (AstroCitizen simplified)",
        f"EventID: {event_id}",
        f"Star: {star}",
        f"Asteroid: {asteroid}",
        f"Observer: {observer}",
        f"SiteLat: {latitude_deg:.6f}",
        f"SiteLon: {longitude_deg:.6f}",
        f"SiteElev_m: {elevation_m:.1f}",
        f"Result: {result}",
        f"D_time_UTC: {d_time_utc or 'na'}",
        f"R_time_UTC: {r_time_utc or 'na'}",
        f"TimeSource: {timesource}",
        f"Instrument: {instrument}",
        f"Notes: {notes or 'na'}",
        "",
        "Upload: occultations.org / iota-hub / SODIS (regional)",
    ]
    return "\n".join(lines) + "\n"


def write_iota_pack(
    out_dir: Path,
    *,
    event_id: str,
    star: str,
    asteroid: str,
    observer: str,
    latitude_deg: float,
    longitude_deg: float,
    elevation_m: float,
    result: str = "positive",
    d_time_utc: str | None = None,
    r_time_utc: str | None = None,
    lc_points: list[dict[str, Any]] | None = None,
    **extra: Any,
) -> Path:
    """Escreve pasta com TXT + meta.json + lc.csv opcional."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in event_id)[:40]
    txt_path = out_dir / f"IOTA-ES_report_{safe}.txt"
    txt_path.write_text(
        format_iota_es_txt(
            event_id=event_id,
            star=star,
            asteroid=asteroid,
            observer=observer,
            latitude_deg=latitude_deg,
            longitude_deg=longitude_deg,
            elevation_m=elevation_m,
            result=result,
            d_time_utc=d_time_utc,
            r_time_utc=r_time_utc,
            timesource=str(extra.get("timesource") or "NTP"),
            instrument=str(extra.get("instrument") or "AstroCitizen"),
            notes=str(extra.get("notes") or ""),
        ),
        encoding="utf-8",
    )
    meta = {
        "network": "iota",
        "event_id": event_id,
        "star": star,
        "asteroid": asteroid,
        "observer": observer,
        "site": {
            "latitude_deg": latitude_deg,
            "longitude_deg": longitude_deg,
            "elevation_m": elevation_m,
        },
        "result": result,
        "d_time_utc": d_time_utc,
        "r_time_utc": r_time_utc,
        "hubs": [
            "https://occultations.org/observing/reporting-observations/",
            "https://iota-hub.com/",
        ],
    }
    (out_dir / "meta.json").write_text(
        json.dumps(meta, indent=2) + "\n", encoding="utf-8"
    )
    if lc_points:
        lc_lines = ["t_utc,signal,signal_err"]
        for p in lc_points:
            lc_lines.append(
                f"{p.get('t_utc', '')},{p.get('y', '')},{p.get('y_err', '')}"
            )
        (out_dir / "lc.csv").write_text("\n".join(lc_lines) + "\n", encoding="utf-8")
    readme = (
        "IOTA report package (AstroCitizen)\n"
        "1. Revise IOTA-ES_report_*.txt\n"
        "2. Anexe lc.csv / graficos se disponivel\n"
        "3. Envie via hub regional (IOTA Hub, SODIS, e-mail Asia)\n"
    )
    (out_dir / "README.txt").write_text(readme, encoding="utf-8")
    return out_dir

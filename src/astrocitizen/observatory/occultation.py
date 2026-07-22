"""Ocultacoes IOTA (PO-D01): previsao IN-PRED + timing IN-TAB + video/LC IN-VID."""

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

VALID_TIMESOURCES = ("NTP", "GPS", "VTI", "manual", "PC")

VIDEO_SUFFIXES = {".ser", ".avi", ".mp4", ".mov", ".mkv", ".mjpg"}


def parse_iota_prediction_text(text: str) -> dict[str, Any]:
    """Parse TXT KEY: value ou CSV (cabecalho event_id,star,asteroid,...)."""
    raw = text.strip()
    if not raw:
        raise DomainError("ficheiro de previsao vazio")

    first = raw.splitlines()[0].strip().lower()
    if "event" in first and "," in first and ("star" in first or "asteroid" in first):
        reader = csv.DictReader(io.StringIO(raw))
        rows = list(reader)
        if not rows:
            raise DomainError("CSV de previsao sem linhas")
        row = {(k or "").strip().lower(): (v or "").strip() for k, v in rows[0].items()}
        return {
            "event_id": row.get("event_id") or row.get("event") or row.get("eventid") or "",
            "star": row.get("star") or row.get("star_name") or "",
            "asteroid": row.get("asteroid") or row.get("body") or "",
            "event_utc": row.get("event_utc") or row.get("utc") or row.get("date") or "",
            "duration_s": _float_or_none(row.get("duration_s") or row.get("duration")),
            "star_ra_deg": _float_or_none(row.get("star_ra") or row.get("ra")),
            "star_dec_deg": _float_or_none(row.get("star_dec") or row.get("dec")),
            "source_format": "csv",
        }

    fields: dict[str, str] = {}
    for line in raw.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            continue
        key, _, val = line.partition(":")
        fields[key.strip().lower().replace(" ", "_")] = val.strip()

    event_id = (
        fields.get("eventid") or fields.get("event_id") or fields.get("event") or ""
    )
    star = fields.get("star") or fields.get("star_name") or ""
    asteroid = fields.get("asteroid") or fields.get("body") or ""
    if not event_id or not star or not asteroid:
        raise DomainError(
            "previsao incompleta: precisa EventID, Star e Asteroid "
            "(TXT KEY: value ou CSV)"
        )
    return {
        "event_id": event_id,
        "star": star,
        "asteroid": asteroid,
        "event_utc": fields.get("eventutc")
        or fields.get("event_utc")
        or fields.get("date_utc")
        or "",
        "duration_s": _float_or_none(fields.get("duration_s") or fields.get("duration")),
        "star_ra_deg": _float_or_none(fields.get("starra") or fields.get("star_ra")),
        "star_dec_deg": _float_or_none(fields.get("stardec") or fields.get("star_dec")),
        "source_format": "txt",
    }


def parse_iota_prediction_file(path: Path) -> dict[str, Any]:
    path = Path(path)
    if not path.is_file():
        raise DomainError(f"ficheiro nao encontrado: {path}")
    return parse_iota_prediction_text(path.read_text(encoding="utf-8", errors="replace"))


def parse_occultation_lc_csv(path: Path) -> list[dict[str, Any]]:
    """CSV t_utc,signal[,signal_err] (PyMovie/Tangra-like simplificado)."""
    path = Path(path)
    if not path.is_file():
        raise DomainError(f"LC CSV nao encontrado: {path}")
    text = path.read_text(encoding="utf-8", errors="replace")
    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        raise DomainError("LC CSV sem cabecalho")
    fields = { (f or "").strip().lower(): f for f in reader.fieldnames }
    t_key = fields.get("t_utc") or fields.get("time") or fields.get("utc") or fields.get("t")
    y_key = (
        fields.get("signal")
        or fields.get("y")
        or fields.get("flux")
        or fields.get("intensity")
        or fields.get("adu")
    )
    e_key = fields.get("signal_err") or fields.get("y_err") or fields.get("err")
    if not t_key or not y_key:
        raise DomainError("LC CSV precisa colunas t_utc/time e signal/y/flux")
    points: list[dict[str, Any]] = []
    for i, row in enumerate(reader):
        t = (row.get(t_key) or "").strip()
        if not t:
            continue
        try:
            y = float(row.get(y_key) or "")
        except ValueError as exc:
            raise DomainError(f"LC linha {i+1}: signal invalido") from exc
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
                "band": "occ",
                "meta": {},
            }
        )
    if len(points) < 2:
        raise DomainError("LC CSV com menos de 2 pontos")
    return points


def suggest_contacts_from_lc(
    points: list[dict[str, Any]], *, drop_frac: float = 0.5
) -> dict[str, str | None]:
    """Heuristica grosseira: D = primeira queda forte, R = recuperacao (AC-122 inicio)."""
    ys = [float(p["y"]) for p in points]
    med = sorted(ys)[len(ys) // 2]
    thr = med * float(drop_frac)
    d_time = None
    r_time = None
    in_event = False
    for p, y in zip(points, ys, strict=True):
        if not in_event and y < thr:
            d_time = str(p["t_utc"])
            in_event = True
        elif in_event and y >= thr and r_time is None:
            r_time = str(p["t_utc"])
            break
    return {"d_time_utc": d_time, "r_time_utc": r_time}


def _float_or_none(val: Any) -> float | None:
    if val is None or val == "":
        return None
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


class ImportIotaPrediction:
    """IN-PRED: guarda artefact + produto occultation_prediction."""

    def __init__(self, archive: Any, store: LocalArtifactStore) -> None:
        self.archive = archive
        self.store = store

    def execute(
        self,
        *,
        workspace_id: UUID,
        path: Path,
        program_id: UUID | None = None,
        site_id: UUID | None = None,
    ) -> AnalysisProduct:
        path = Path(path)
        parsed = parse_iota_prediction_file(path)
        uri = self.store.put(path, key=f"import/iota_pred/{path.name}")
        product = AnalysisProduct(
            id=new_id(),
            workspace_id=workspace_id,
            program_id=program_id,
            product_type="occultation_prediction",
            version_num=1,
            is_publishable=False,
            parameters={
                "channel": "IN-PRED",
                "source_uri": uri,
                "source_path": str(path),
                "site_id": str(site_id) if site_id else None,
                **parsed,
            },
            summary={
                "event_id": parsed["event_id"],
                "star": parsed["star"],
                "asteroid": parsed["asteroid"],
                "event_utc": parsed.get("event_utc") or "",
            },
            state="ready",
        )
        return self.archive.save_analysis_product(product)


class RegisterOccultationTiming:
    """IN-TAB (+ IN-VID): Observation + occultation_timing + video/LC opcionais."""

    def __init__(self, archive: Any, store: LocalArtifactStore | None = None) -> None:
        self.archive = archive
        self.store = store

    def execute(
        self,
        *,
        workspace_id: UUID,
        event_id: str,
        star: str,
        asteroid: str,
        result: str = "positive",
        d_time_utc: str | None = None,
        r_time_utc: str | None = None,
        timesource: str = "NTP",
        site_id: UUID | None = None,
        program_id: UUID | None = None,
        prediction_product_id: UUID | None = None,
        observer: str = "AstroCitizen",
        notes: str = "",
        observed_at_utc: str | None = None,
        video_path: Path | None = None,
        lc_csv_path: Path | None = None,
        suggest_contacts: bool = False,
    ) -> AnalysisProduct:
        event_id = (event_id or "").strip()
        star = (star or "").strip()
        asteroid = (asteroid or "").strip()
        if not event_id or not star or not asteroid:
            raise DomainError("event_id, star e asteroid obrigatorios")
        result = (result or "positive").strip().lower()
        if result not in ("positive", "negative", "missed"):
            raise DomainError("result deve ser positive|negative|missed")
        ts = (timesource or "NTP").strip() or "NTP"
        if ts not in VALID_TIMESOURCES:
            raise DomainError(
                f"timesource invalido: {ts} (use {', '.join(VALID_TIMESOURCES)})"
            )

        lc_points: list[dict[str, Any]] = []
        suggested: dict[str, str | None] = {}
        if lc_csv_path is not None:
            lc_points = parse_occultation_lc_csv(Path(lc_csv_path))
            if suggest_contacts:
                suggested = suggest_contacts_from_lc(lc_points)
                d_time_utc = d_time_utc or suggested.get("d_time_utc")
                r_time_utc = r_time_utc or suggested.get("r_time_utc")

        if result == "positive" and not d_time_utc and not r_time_utc:
            raise DomainError("positive requer d_time_utc e/ou r_time_utc")

        when = observed_at_utc or d_time_utc or r_time_utc or utc_now_iso()
        obs_id = new_id()
        self.archive.create_observation(
            observation_id=obs_id,
            workspace_id=workspace_id,
            observed_at_utc=when,
            site_id=site_id,
            program_id=program_id,
            simulated=False,
            notes=f"iota:{event_id} {result}",
        )

        video_uri = None
        lc_uri = None
        if video_path is not None:
            if self.store is None:
                raise DomainError("store necessario para anexar video")
            vpath = Path(video_path)
            if not vpath.is_file():
                raise DomainError(f"video nao encontrado: {vpath}")
            suf = vpath.suffix.lower()
            if suf not in VIDEO_SUFFIXES:
                raise DomainError(
                    f"extensao video nao suportada: {suf} "
                    f"(use {sorted(VIDEO_SUFFIXES)})"
                )
            video_uri = self.store.put(vpath, key=f"import/iota_vid/{vpath.name}")
            kind = "video_ser" if suf == ".ser" else "video_occ"
            self.archive.save_artifact(
                artifact_id=new_id(),
                workspace_id=workspace_id,
                kind=kind,
                uri=video_uri,
                filename=vpath.name,
                observation_id=obs_id,
                size_bytes=vpath.stat().st_size,
            )

        if lc_csv_path is not None:
            if self.store is None:
                raise DomainError("store necessario para anexar LC")
            lpath = Path(lc_csv_path)
            lc_uri = self.store.put(lpath, key=f"import/iota_lc/{lpath.name}")
            self.archive.save_artifact(
                artifact_id=new_id(),
                workspace_id=workspace_id,
                kind="occultation_lc",
                uri=lc_uri,
                filename=lpath.name,
                observation_id=obs_id,
                size_bytes=lpath.stat().st_size,
            )

        product = AnalysisProduct(
            id=new_id(),
            workspace_id=workspace_id,
            program_id=program_id,
            product_type="occultation_timing",
            version_num=1,
            is_publishable=False,
            parameters={
                "channel": "IN-TAB",
                "event_id": event_id,
                "star": star,
                "asteroid": asteroid,
                "result": result,
                "d_time_utc": d_time_utc,
                "r_time_utc": r_time_utc,
                "timesource": ts,
                "observer": observer,
                "notes": notes,
                "site_id": str(site_id) if site_id else None,
                "prediction_product_id": (
                    str(prediction_product_id) if prediction_product_id else None
                ),
                "observation_id": str(obs_id),
                "video_uri": video_uri,
                "lc_uri": lc_uri,
                "n_lc_points": len(lc_points),
                "suggested_contacts": suggested or None,
            },
            summary={
                "event_id": event_id,
                "star": star,
                "asteroid": asteroid,
                "result": result,
                "d_time_utc": d_time_utc or "",
                "r_time_utc": r_time_utc or "",
                "timesource": ts,
                "has_video": video_uri is not None,
                "n_lc_points": len(lc_points),
            },
            state="ready",
        )
        product = self.archive.save_analysis_product(product)
        self.archive.link_product_observation(product.id, obs_id)
        if lc_points:
            self.archive.save_measurement_points(product.id, lc_points)
        return product

"""Ocultacoes IOTA (PO-D01): previsao IN-PRED + timing IN-TAB."""

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


def parse_iota_prediction_text(text: str) -> dict[str, Any]:
    """Parse TXT KEY: value ou CSV (cabecalho event_id,star,asteroid,...)."""
    raw = text.strip()
    if not raw:
        raise DomainError("ficheiro de previsao vazio")

    # CSV?
    first = raw.splitlines()[0].strip().lower()
    if "event" in first and "," in first and ("star" in first or "asteroid" in first):
        reader = csv.DictReader(io.StringIO(raw))
        rows = list(reader)
        if not rows:
            raise DomainError("CSV de previsao sem linhas")
        row = { (k or "").strip().lower(): (v or "").strip() for k, v in rows[0].items() }
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
        fields.get("eventid")
        or fields.get("event_id")
        or fields.get("event")
        or ""
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
        uri = self.store.put(
            path, key=f"import/iota_pred/{path.name}"
        )
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
    """IN-TAB: Observation + produto occultation_timing (contactos D/R)."""

    def __init__(self, archive: Any) -> None:
        self.archive = archive

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
    ) -> AnalysisProduct:
        event_id = (event_id or "").strip()
        star = (star or "").strip()
        asteroid = (asteroid or "").strip()
        if not event_id or not star or not asteroid:
            raise DomainError("event_id, star e asteroid obrigatorios")
        result = (result or "positive").strip().lower()
        if result not in ("positive", "negative", "missed"):
            raise DomainError("result deve ser positive|negative|missed")
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
                "timesource": timesource,
                "observer": observer,
                "notes": notes,
                "site_id": str(site_id) if site_id else None,
                "prediction_product_id": (
                    str(prediction_product_id) if prediction_product_id else None
                ),
                "observation_id": str(obs_id),
            },
            summary={
                "event_id": event_id,
                "star": star,
                "asteroid": asteroid,
                "result": result,
                "d_time_utc": d_time_utc or "",
                "r_time_utc": r_time_utc or "",
            },
            state="ready",
        )
        product = self.archive.save_analysis_product(product)
        self.archive.link_product_observation(product.id, obs_id)
        return product

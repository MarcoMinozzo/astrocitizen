"""Payloads canónicos para push SaaS (AC-222 / API_ALVO)."""

from __future__ import annotations

from typing import Any
from uuid import UUID


def observation_canonical(obs: Any) -> dict[str, Any]:
    """ObservationRecord → JSON canónico (sem caminhos locais)."""
    return {
        "id": str(obs.id),
        "workspace_id": str(obs.workspace_id),
        "observed_at_utc": obs.observed_at_utc,
        "site_id": str(obs.site_id) if obs.site_id else None,
        "session_id": str(obs.session_id) if obs.session_id else None,
        "block_id": str(obs.block_id) if obs.block_id else None,
        "program_id": str(obs.program_id) if obs.program_id else None,
        "target_id": str(obs.target_id) if obs.target_id else None,
        "instrument_config_id": (
            str(obs.instrument_config_id) if obs.instrument_config_id else None
        ),
        "state": obs.state,
        "camera_backend": obs.camera_backend,
        "simulated": bool(obs.simulated),
        "meteo_manual": bool(obs.meteo_manual),
        "headers_summary": dict(obs.headers_summary or {}),
        "notes": obs.notes or "",
        "version": int(obs.version),
    }


def network_submission_canonical(sub: Any) -> dict[str, Any]:
    """NetworkSubmission → JSON canónico (URI como string; sem ficheiro)."""
    return {
        "id": str(sub.id),
        "workspace_id": str(sub.workspace_id),
        "network": sub.network,
        "status": sub.status,
        "artifact_uri": sub.artifact_uri,
        "product_id": str(sub.product_id) if sub.product_id else None,
        "payload_summary": dict(sub.payload_summary or {}),
        "remote_ack": sub.remote_ack,
        "error": sub.error,
        "created_at": sub.created_at,
        "updated_at": sub.updated_at,
        "version": int(sub.version),
    }


def catalog_object_canonical(obj: Any) -> dict[str, Any]:
    """CatalogObject → JSON canónico para o catálogo mestre SaaS."""
    return {
        "id": str(obj.id),
        "workspace_id": str(obj.workspace_id),
        "query_name": obj.query_name,
        "designation": obj.designation,
        "ra_deg": obj.ra_deg,
        "dec_deg": obj.dec_deg,
        "sections": dict(obj.sections or {}),
        "sources": list(obj.sources or []),
        "fetched_at": obj.fetched_at,
        "updated_at": obj.updated_at,
        "version": int(obj.version),
    }


def batch_operation(
    *,
    client_op_id: UUID,
    entity: str,
    operation: str,
    payload: dict[str, Any],
    client_timestamp_utc: str,
) -> dict[str, Any]:
    return {
        "client_op_id": str(client_op_id),
        "entity": entity,
        "operation": operation,
        "payload": payload,
        "client_timestamp_utc": client_timestamp_utc,
    }

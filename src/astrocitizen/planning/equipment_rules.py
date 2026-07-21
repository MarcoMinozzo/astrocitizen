"""Validacao de configuracao instrumental no plano (RN-030...035)."""

from __future__ import annotations

from uuid import UUID

from astrocitizen.inventory.models import Equipment, InstrumentConfig


REQUIRED_ROLES = ("camera", "mount")


def validate_instrument_config(
    config: InstrumentConfig | None,
    equipment_by_id: dict[UUID, Equipment],
    *,
    planning_only: bool = True,
) -> tuple[bool, str | None]:
    """Retorna (ok, motivo). RN-055: planning_only nao exige backend conectado."""
    if config is None:
        return False, "configuracao instrumental ausente (RN-030)"

    for role in REQUIRED_ROLES:
        eq_id = config.items.get(role)
        if eq_id is None:
            return False, f"role '{role}' em falta na configuracao (RN-033)"
        eq = equipment_by_id.get(eq_id)
        if eq is None:
            return False, f"equipamento {role} inexistente"
        if not eq.available:
            return False, f"equipamento '{eq.name}' indisponivel (RN-035)"
        if not planning_only and role == "camera" and not eq.backend:
            return False, "camera sem backend seleccionado (RN-032)"
    return True, None

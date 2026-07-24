"""Provider TNS — wrapper report (D-012)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from astrocitizen.contribution.tns import format_tns_at_report, write_tns_report
from astrocitizen.domain.observation import Observation
from astrocitizen.integrations.base import BaseObservatoryProvider
from astrocitizen.shared.errors import DomainError


class TnsProvider(BaseObservatoryProvider):
    name = "tns"
    features = frozenset({"prepare_transient"})

    def prepare_transient(
        self, observation: Observation, *, out_path: Path, **kwargs: Any
    ) -> Path:
        if observation.ra_deg is None or observation.dec_deg is None:
            raise DomainError("TNS: ra_deg/dec_deg obrigatorios", rule_id="D-012")
        groupid = kwargs.get("groupid", observation.extra.get("groupid"))
        if groupid is None:
            raise DomainError("TNS: groupid obrigatorio", rule_id="D-012")
        discovery_mag = (
            observation.mag
            if observation.mag is not None
            else kwargs.get("discovery_mag")
        )
        if discovery_mag is None:
            raise DomainError("TNS: mag / discovery_mag obrigatorio", rule_id="D-012")
        report = format_tns_at_report(
            ra_deg=float(observation.ra_deg),
            dec_deg=float(observation.dec_deg),
            groupid=int(groupid),
            reporter=str(
                observation.observer or kwargs.get("reporter") or "AstroCitizen"
            ),
            discovery_mag=float(discovery_mag),
            filter_value=str(
                observation.filter_name or kwargs.get("filter_value") or "Clear"
            ),
            instrument_value=str(
                observation.instrument or kwargs.get("instrument_value") or "Other"
            ),
            limiting_flux=kwargs.get("limiting_flux"),
            internal_name=observation.object_name,
        )
        return write_tns_report(Path(out_path), report)

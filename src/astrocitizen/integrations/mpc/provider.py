"""Provider MPC — wrapper ADES (D-012)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from astrocitizen.contribution.mpc import write_ades_psv
from astrocitizen.domain.observation import Observation
from astrocitizen.integrations.base import BaseObservatoryProvider
from astrocitizen.shared.errors import DomainError


class MpcProvider(BaseObservatoryProvider):
    name = "mpc"
    features = frozenset({"prepare_astrometry"})

    def prepare_astrometry(
        self, observation: Observation, *, out_path: Path, **kwargs: Any
    ) -> Path:
        code = observation.observatory_code or kwargs.get("observatory_code")
        if not code:
            raise DomainError("MPC: observatory_code obrigatorio", rule_id="D-012")
        if observation.ra_deg is None or observation.dec_deg is None:
            raise DomainError("MPC: ra_deg/dec_deg obrigatorios", rule_id="D-012")
        epoch = kwargs.get("epoch_utc") or observation.extra.get("epoch_utc")
        if not epoch:
            raise DomainError("MPC: epoch_utc obrigatorio", rule_id="D-012")
        obs_row = {
            "epoch_utc": str(epoch),
            "ra_deg": float(observation.ra_deg),
            "dec_deg": float(observation.dec_deg),
            "mag": observation.mag,
            "band": observation.filter_name or kwargs.get("band") or "R",
        }
        return write_ades_psv(
            Path(out_path),
            designation=observation.object_name,
            observatory_code=str(code),
            observations=[obs_row],
            submitter=str(kwargs.get("submitter") or "AstroCitizen"),
        )

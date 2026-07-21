"""Factory de backends de plate-solve."""

from __future__ import annotations

from typing import Any

from astrocitizen.adapters.platesolve.nova import NovaAstrometryNetSolver
from astrocitizen.adapters.platesolve.solve_field import SolveFieldPlateSolver
from astrocitizen.adapters.platesolve.synthetic import SyntheticPlateSolver
from astrocitizen.shared.errors import DomainError


def create_plate_solver(
    backend: str = "auto",
    *,
    api_key: str | None = None,
    nova_dry_run: bool = True,
) -> Any:
    """Cria solver: auto | solve-field | nova | synthetic."""
    backend = (backend or "auto").lower()
    if backend == "synthetic":
        return SyntheticPlateSolver()
    if backend == "solve-field":
        return SolveFieldPlateSolver()
    if backend == "nova":
        return NovaAstrometryNetSolver(
            api_key=api_key or "dry-run-key",
            dry_run=nova_dry_run,
        )
    if backend == "auto":
        sf = SolveFieldPlateSolver()
        if sf.available():
            return sf
        return SyntheticPlateSolver()
    raise DomainError(f"backend plate-solve desconhecido: {backend}")

"""Adapters plate-solve (AC-110)."""

from astrocitizen.adapters.platesolve.factory import create_plate_solver
from astrocitizen.adapters.platesolve.nova import NovaAstrometryNetSolver
from astrocitizen.adapters.platesolve.solve_field import SolveFieldPlateSolver
from astrocitizen.adapters.platesolve.synthetic import SyntheticPlateSolver

__all__ = [
    "NovaAstrometryNetSolver",
    "SolveFieldPlateSolver",
    "SyntheticPlateSolver",
    "create_plate_solver",
]

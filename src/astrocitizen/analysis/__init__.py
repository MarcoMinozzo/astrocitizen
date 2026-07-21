"""Analise (fotometria, espectro, astrometria, blink, plate-solve)."""

from astrocitizen.analysis.astrometry import MeasureAstrometry
from astrocitizen.analysis.blink import BlinkDiff
from astrocitizen.analysis.photometry import AperturePhotometry
from astrocitizen.analysis.platesolve import PlateSolve
from astrocitizen.analysis.spectroscopy import ExtractSpectrum1D

__all__ = [
    "AperturePhotometry",
    "ExtractSpectrum1D",
    "MeasureAstrometry",
    "BlinkDiff",
    "PlateSolve",
]

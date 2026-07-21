"""Analise (fotometria, espectro, astrometria, blink, plate-solve, solar)."""

from astrocitizen.analysis.astrometry import MeasureAstrometry
from astrocitizen.analysis.blink import BlinkDiff
from astrocitizen.analysis.photometry import AperturePhotometry
from astrocitizen.analysis.platesolve import PlateSolve
from astrocitizen.analysis.solar import CountSunspots
from astrocitizen.analysis.spectroscopy import ExtractSpectrum1D

__all__ = [
    "AperturePhotometry",
    "ExtractSpectrum1D",
    "MeasureAstrometry",
    "BlinkDiff",
    "PlateSolve",
    "CountSunspots",
]

"""Analise (fotometria, espectro, astrometria, blink, plate-solve, solar)."""

from astrocitizen.analysis.astrometry import MeasureAstrometry
from astrocitizen.analysis.blink import BlinkDiff
from astrocitizen.analysis.photometry import AperturePhotometry
from astrocitizen.analysis.platesolve import PlateSolve
from astrocitizen.analysis.solar import CountSunspots
from astrocitizen.analysis.spectroscopy import ExtractSpectrum1D
from astrocitizen.analysis.spectrum_report import InterpretSpectrum
from astrocitizen.analysis.wavelength_calib import CalibrateWavelength

__all__ = [
    "AperturePhotometry",
    "CalibrateWavelength",
    "ExtractSpectrum1D",
    "InterpretSpectrum",
    "MeasureAstrometry",
    "BlinkDiff",
    "PlateSolve",
    "CountSunspots",
]

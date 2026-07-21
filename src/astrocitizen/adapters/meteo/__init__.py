"""Adapters de meteorologia e radar."""

from astrocitizen.adapters.meteo.manual import ManualMeteo
from astrocitizen.adapters.meteo.open_meteo import OpenMeteo
from astrocitizen.adapters.meteo.rainviewer import RainViewerRadar

__all__ = ["ManualMeteo", "OpenMeteo", "RainViewerRadar"]

"""Adapters de meteorologia."""

from astrocitizen.adapters.meteo.manual import ManualMeteo
from astrocitizen.adapters.meteo.open_meteo import OpenMeteo

__all__ = ["ManualMeteo", "OpenMeteo"]

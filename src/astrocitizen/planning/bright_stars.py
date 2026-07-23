"""Catalogo leve de estrelas brilhantes (AC-079b) — offline, D-010.

~50 estrelas mais brilhantes (Hipparcos / valores J2000 approx).
Nao e um planetario: so contexto visual na carta do plano.
"""

from __future__ import annotations

from typing import NamedTuple


class BrightStar(NamedTuple):
    name: str
    ra_deg: float
    dec_deg: float
    vmag: float


# Fonte: Hipparcos brightest (RA/Dec graus ICRS approx).
BRIGHT_STARS: tuple[BrightStar, ...] = (
    BrightStar("Sirius", 101.287, -16.716, -1.46),
    BrightStar("Canopus", 95.988, -52.696, -0.74),
    BrightStar("Rigil Kent", 219.902, -60.834, -0.27),
    BrightStar("Arcturus", 213.915, 19.182, -0.05),
    BrightStar("Vega", 279.234, 38.783, 0.03),
    BrightStar("Capella", 79.172, 45.998, 0.08),
    BrightStar("Rigel", 78.634, -8.202, 0.13),
    BrightStar("Procyon", 114.825, 5.225, 0.34),
    BrightStar("Achernar", 24.429, -57.237, 0.46),
    BrightStar("Betelgeuse", 88.793, 7.407, 0.42),
    BrightStar("Hadar", 210.956, -60.373, 0.61),
    BrightStar("Altair", 297.696, 8.868, 0.77),
    BrightStar("Acrux", 186.650, -63.099, 0.77),
    BrightStar("Aldebaran", 68.980, 16.509, 0.86),
    BrightStar("Antares", 247.352, -26.432, 0.96),
    BrightStar("Spica", 201.298, -11.161, 0.97),
    BrightStar("Pollux", 116.329, 28.026, 1.14),
    BrightStar("Fomalhaut", 344.413, -29.622, 1.16),
    BrightStar("Deneb", 310.358, 45.280, 1.25),
    BrightStar("Mimosa", 191.930, -59.689, 1.25),
    BrightStar("Regulus", 152.093, 11.967, 1.35),
    BrightStar("Adhara", 104.656, -28.972, 1.50),
    BrightStar("Castor", 113.650, 31.888, 1.58),
    BrightStar("Shaula", 263.402, -37.104, 1.62),
    BrightStar("Bellatrix", 81.283, 6.350, 1.64),
    BrightStar("Elnath", 81.573, 28.608, 1.65),
    BrightStar("Miaplacidus", 138.300, -69.717, 1.67),
    BrightStar("Alnilam", 84.053, -1.202, 1.70),
    BrightStar("Alnair", 332.058, -46.961, 1.74),
    BrightStar("Alnitak", 85.190, -1.943, 1.77),
    BrightStar("Alioth", 193.507, 55.960, 1.77),
    BrightStar("Mirfak", 51.081, 49.861, 1.79),
    BrightStar("Dubhe", 165.932, 61.751, 1.79),
    BrightStar("Wezen", 107.097, -26.393, 1.84),
    BrightStar("Kaus Australis", 276.043, -34.384, 1.85),
    BrightStar("Avior", 125.628, -59.510, 1.86),
    BrightStar("Alkaid", 206.885, 49.313, 1.86),
    BrightStar("Menkalinan", 89.882, 44.948, 1.90),
    BrightStar("Atria", 252.166, -69.028, 1.92),
    BrightStar("Alhena", 99.428, 16.399, 1.93),
    BrightStar("Peacock", 306.412, -56.735, 1.94),
    BrightStar("Alsephina", 131.179, -54.709, 1.96),
    BrightStar("Mirzam", 95.675, -17.956, 1.98),
    BrightStar("Alphard", 141.897, -8.659, 2.00),
    BrightStar("Polaris", 37.955, 89.264, 1.98),
    BrightStar("Hamal", 31.793, 23.462, 2.00),
    BrightStar("Algieba", 154.173, 19.842, 2.01),
    BrightStar("Diphda", 10.897, -17.987, 2.04),
    BrightStar("Nunki", 283.816, -26.297, 2.05),
    BrightStar("Menkent", 204.972, -36.370, 2.06),
)


def stars_brighter_than(max_vmag: float = 2.5) -> tuple[BrightStar, ...]:
    return tuple(s for s in BRIGHT_STARS if s.vmag <= max_vmag)

"""Ficha celeste unificada — secções por domínio físico (AC-235)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

# Ordem estável das secções na UI
SECTION_ORDER: tuple[str, ...] = (
    "identity",
    "position",
    "photometry",
    "variability",
    "astrometry",
    "spectroscopy",
    "identifiers",
    "provenance",
)

SECTION_LABELS: dict[str, str] = {
    "identity": "Identidade",
    "position": "Posicao",
    "photometry": "Fotometria",
    "variability": "Variabilidade",
    "astrometry": "Astrometria / movimento proprio",
    "spectroscopy": "Espectroscopia",
    "identifiers": "Identificadores",
    "provenance": "Proveniencia (fontes)",
}

# Campos por secção (chave → rótulo UI)
SECTION_FIELDS: dict[str, tuple[tuple[str, str], ...]] = {
    "identity": (
        ("designation", "Designacao"),
        ("query", "Nome pesquisado"),
        ("object_type", "Tipo de objecto"),
    ),
    "position": (
        ("ra_deg", "RA (deg, ICRS)"),
        ("dec_deg", "Dec (deg, ICRS)"),
        ("coord_frame", "Sistema"),
    ),
    "photometry": (
        ("mag_max", "Mag max"),
        ("mag_min", "Mag min"),
        ("gmag", "G (Gaia)"),
        ("band_notes", "Notas de banda"),
    ),
    "variability": (
        ("variability_type", "Tipo VSX"),
        ("period", "Periodo (d)"),
        ("auid", "AUID"),
    ),
    "astrometry": (
        ("gaia_source_id", "Gaia source_id"),
        ("parallax_mas", "Paralaxe (mas)"),
        ("pmra", "PM RA (mas/a)"),
        ("pmdec", "PM Dec (mas/a)"),
    ),
    "spectroscopy": (
        ("spectral_type", "Tipo espectral"),
        ("resolution_notes", "Notas"),
    ),
    "identifiers": (
        ("simbad", "SIMBAD"),
        ("sesame", "Sesame"),
        ("vsx", "VSX"),
        ("vizier", "VizieR"),
        ("other_ids", "Outros"),
    ),
    "provenance": (
        ("sources", "APIs consultadas"),
        ("fetched_at", "Ultima actualizacao"),
    ),
}


def empty_sections() -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for key in SECTION_ORDER:
        out[key] = {field_key: None for field_key, _ in SECTION_FIELDS[key]}
    return out


def dossier_from_resolved(
    resolved: dict[str, Any],
    *,
    query: str,
    fetched_at: str,
) -> dict[str, dict[str, Any]]:
    """Constrói secções a partir do payload CatalogResolveService."""
    ids = dict(resolved.get("external_ids") or {})
    sections = empty_sections()

    sections["identity"]["designation"] = resolved.get("designation") or query
    sections["identity"]["query"] = query
    sections["identity"]["object_type"] = (
        ids.get("variability_type") or ids.get("otype") or None
    )

    sections["position"]["ra_deg"] = resolved.get("ra_deg")
    sections["position"]["dec_deg"] = resolved.get("dec_deg")
    sections["position"]["coord_frame"] = "ICRS J2000"

    sections["photometry"]["mag_max"] = ids.get("mag_max")
    sections["photometry"]["mag_min"] = ids.get("mag_min")
    sections["photometry"]["gmag"] = ids.get("gmag")

    sections["variability"]["variability_type"] = ids.get("variability_type")
    sections["variability"]["period"] = ids.get("period")
    sections["variability"]["auid"] = ids.get("auid")

    sections["astrometry"]["gaia_source_id"] = ids.get("gaia_source_id")
    sections["astrometry"]["parallax_mas"] = ids.get("parallax_mas")
    sections["astrometry"]["pmra"] = ids.get("pmra")
    sections["astrometry"]["pmdec"] = ids.get("pmdec")

    # Espectroscopia: ainda pouco nas APIs actuais — reservado
    sections["spectroscopy"]["spectral_type"] = ids.get("spectral_type") or ids.get(
        "sptype"
    )

    sections["identifiers"]["simbad"] = ids.get("simbad")
    sections["identifiers"]["sesame"] = ids.get("sesame")
    sections["identifiers"]["vsx"] = ids.get("vsx")
    sections["identifiers"]["vizier"] = ids.get("vizier")
    skip = {
        "simbad",
        "sesame",
        "vsx",
        "vizier",
        "auid",
        "variability_type",
        "period",
        "mag_max",
        "mag_min",
        "gmag",
        "otype",
        "gaia_source_id",
        "parallax_mas",
        "pmra",
        "pmdec",
        "source",
        "spectral_type",
        "sptype",
    }
    other = {k: v for k, v in ids.items() if k not in skip and v is not None}
    sections["identifiers"]["other_ids"] = other or None

    sources = resolved.get("sources") or []
    sections["provenance"]["sources"] = ", ".join(sources) if sources else None
    sections["provenance"]["fetched_at"] = fetched_at
    return sections


@dataclass(slots=True)
class CatalogObject:
    """Objecto do nosso catálogo (ficha persistida)."""

    id: UUID
    workspace_id: UUID
    query_name: str
    designation: str
    ra_deg: float | None = None
    dec_deg: float | None = None
    sections: dict[str, dict[str, Any]] = field(default_factory=empty_sections)
    sources: list[str] = field(default_factory=list)
    fetched_at: str = ""
    updated_at: str = ""
    version: int = 1

    def field_value(self, section: str, key: str) -> Any:
        return (self.sections.get(section) or {}).get(key)

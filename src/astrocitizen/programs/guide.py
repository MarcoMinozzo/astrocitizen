"""Guia do programa activo: passos PO-* -> navegacao GUI (sem Qt)."""

from __future__ import annotations

from typing import Any

# Mapeamento passo de workflow -> destino na shell
STEP_NAV: dict[str, dict[str, str]] = {
    "plan_targets": {
        "area": "Configurar",
        "hub_tab": "Alvos",
        "label": "Gerir alvos",
    },
    "plan_fields": {
        "area": "Configurar",
        "hub_tab": "Alvos",
        "label": "Gerir campos",
    },
    "plan_ephemeris": {
        "area": "Noite",
        "hub_tab": "Planos",
        "label": "Planos / efemerides",
    },
    "meteo_snapshot": {
        "area": "Noite",
        "hub_tab": "Meteo / radar",
        "label": "Meteo",
    },
    "evaluate_thresholds": {
        "area": "Noite",
        "hub_tab": "Meteo / radar",
        "label": "Meteo",
    },
    "annotate_blocks": {
        "area": "Noite",
        "hub_tab": "Planos",
        "label": "Planos",
    },
    "acquire_lights": {
        "area": "Observatorio",
        "hub_tab": "Sessao",
        "label": "Sessao / captura",
    },
    "acquire_spectrum_2d": {
        "area": "Observatorio",
        "hub_tab": "Sessao",
        "label": "Sessao / espectro",
    },
    "acquire_pair": {
        "area": "Observatorio",
        "hub_tab": "Sessao",
        "label": "Sessao / par",
    },
    "acquire_nonsidereal": {
        "area": "Observatorio",
        "hub_tab": "Observar",
        "label": "Observar",
    },
    "acquire_timed": {
        "area": "Observatorio",
        "hub_tab": "Timing",
        "label": "Timing / ocultacao",
    },
    "acquire_white_light": {
        "area": "Observatorio",
        "hub_tab": "Observar",
        "label": "Observar (solar)",
    },
    "acquire_calibration_frames": {
        "area": "Observatorio",
        "hub_tab": "Sessao",
        "label": "Calibracao",
    },
    "import_prediction": {
        "area": "Observatorio",
        "hub_tab": "Timing",
        "label": "Import predicao",
    },
    "import_radio_series": {
        "area": "Observatorio",
        "hub_tab": "Importar",
        "analyze_tab": "Radio",
        "label": "Importar radio (serie)",
    },
    "import_radio_spectrum": {
        "area": "Observatorio",
        "hub_tab": "Importar",
        "analyze_tab": "Radio",
        "label": "Importar radio (espectro)",
    },
    "import_radio_scan": {
        "area": "Observatorio",
        "hub_tab": "Importar",
        "analyze_tab": "Radio",
        "label": "Importar radio (scan)",
    },
    "log_radio_lab": {
        "area": "Observatorio",
        "hub_tab": "Importar",
        "analyze_tab": "Radio",
        "label": "Lab notes radio",
    },
    "import_echelle_orders": {
        "area": "Observatorio",
        "hub_tab": "Importar",
        "label": "Especialidades",
    },
    "import_speckle_cube": {
        "area": "Observatorio",
        "hub_tab": "Importar",
        "label": "Especialidades",
    },
    "import_polar_set": {
        "area": "Observatorio",
        "hub_tab": "Importar",
        "label": "Especialidades",
    },
    "calibrate": {
        "area": "Observatorio",
        "hub_tab": "Importar",
        "label": "Importar / calib",
    },
    "build_masters": {
        "area": "Observatorio",
        "hub_tab": "Importar",
        "label": "Masters",
    },
    "apply_calibration": {
        "area": "Observatorio",
        "hub_tab": "Importar",
        "label": "Aplicar calib",
    },
    "aperture_photometry": {
        "area": "Analisar",
        "analyze_tab": "Fotometria",
        "label": "Fotometria",
    },
    "extract_spectrum_1d": {
        "area": "Analisar",
        "analyze_tab": "Espectro",
        "label": "Espectro 1D",
    },
    "interpret_spectrum": {
        "area": "Analisar",
        "analyze_tab": "Espectro",
        "label": "Espectro",
    },
    "wavelength_linear": {
        "area": "Analisar",
        "analyze_tab": "Espectro",
        "label": "Espectro",
    },
    "line_measures": {
        "area": "Analisar",
        "analyze_tab": "Espectro",
        "label": "Espectro",
    },
    "compare_epochs": {
        "area": "Analisar",
        "analyze_tab": "Espectro",
        "label": "Espectro",
    },
    "plate_solve": {
        "area": "Analisar",
        "analyze_tab": "Blink / Astrom",
        "label": "Plate-solve",
    },
    "measure_astrometry": {
        "area": "Analisar",
        "analyze_tab": "Blink / Astrom",
        "label": "Astrometria",
    },
    "blink_diff": {
        "area": "Analisar",
        "analyze_tab": "Blink / Astrom",
        "label": "Blink",
    },
    "reduce_contacts": {
        "area": "Observatorio",
        "hub_tab": "Timing",
        "label": "Contactos",
    },
    "log_visual": {
        "area": "Observatorio",
        "hub_tab": "Observar",
        "label": "Log visual",
    },
    "log_double_measure": {
        "area": "Observatorio",
        "hub_tab": "Observar",
        "analyze_tab": "Duplas (PO-G01)",
        "label": "Medida dupla",
    },
    "review_notes": {
        "area": "Arquivo",
        "label": "Arquivo",
    },
    "review_timeseries": {
        "area": "Analisar",
        "analyze_tab": "Curvas",
        "label": "Curvas",
    },
    "review_orders": {
        "area": "Arquivo",
        "label": "Arquivo",
    },
    "review_frames": {
        "area": "Arquivo",
        "label": "Arquivo",
    },
    "review_pol": {
        "area": "Arquivo",
        "label": "Arquivo",
    },
    "count_sunspots": {
        "area": "Analisar",
        "label": "Analisar",
    },
    "safety_checklist": {
        "area": "Observatorio",
        "hub_tab": "Observar",
        "label": "Seguranca solar",
    },
    "export_aavso": {
        "area": "Contribuir",
        "network": "aavso",
        "label": "Export AAVSO",
    },
    "export_exoclock": {
        "area": "Contribuir",
        "network": "exoclock",
        "label": "Export ExoClock",
    },
    "export_mpc_ades": {
        "area": "Contribuir",
        "network": "mpc",
        "label": "Export MPC",
    },
    "export_tns": {
        "area": "Contribuir",
        "network": "tns",
        "label": "Export TNS",
    },
    "export_bess": {
        "area": "Contribuir",
        "network": "bess",
        "label": "Export BeSS",
    },
    "export_aras": {
        "area": "Contribuir",
        "network": "bess",
        "label": "Export ARAS/BeSS",
    },
    "export_iota_pack": {
        "area": "Contribuir",
        "network": "iota",
        "label": "Export IOTA",
    },
    "export_solar_report": {
        "area": "Contribuir",
        "label": "Contribuir (solar)",
    },
    "export_radio_csv": {
        "area": "Arquivo",
        "label": "Arquivo / radio",
    },
}


def normalize_network_key(name: str) -> str | None:
    """Mapeia nome de rede do template -> chave tab Contribuir."""
    raw = (name or "").strip().lower()
    if not raw:
        return None
    key = raw.replace(" ", "").replace("_", "-")
    aliases = {
        "aavso": "aavso",
        "aavso-visual": "aavso",
        "exoclock": "exoclock",
        "mpc": "mpc",
        "tns": "tns",
        "bess": "bess",
        "aras": "bess",
        "iota": "iota",
    }
    if key in aliases:
        return aliases[key]
    for prefix, dest in aliases.items():
        if key.startswith(prefix):
            return dest
    return None


def resolve_export_networks(
    program: Any,
    workflow: dict[str, Any] | None,
    template: Any | None = None,
) -> list[str]:
    """Redes de export: program.export_networks > workflow > template."""
    for source in (
        getattr(program, "export_networks", None),
        (workflow or {}).get("networks"),
        getattr(template, "default_networks", None) if template else None,
    ):
        if source:
            return [str(x) for x in source]
    return []


def step_nav_rows(workflow: dict[str, Any] | None) -> list[dict[str, str]]:
    """Lista passos com destino de navegacao (se conhecido)."""
    if not workflow:
        return []
    rows: list[dict[str, str]] = []
    for step in workflow.get("steps") or []:
        nav = dict(STEP_NAV.get(step, {"area": "Observatorio", "label": step}))
        nav["step"] = step
        nav.setdefault("label", step)
        rows.append(nav)
    return rows


def target_link_rows(links: list[tuple[Any, str, int]]) -> list[list[str]]:
    """Linhas [designation, role, type, id8] para tabela GUI."""
    rows: list[list[str]] = []
    for target, role, _order in links:
        rows.append(
            [
                str(getattr(target, "designation", "")),
                str(role),
                str(getattr(target, "target_type", "") or "-"),
                str(getattr(target, "id", ""))[:8],
            ]
        )
    return rows

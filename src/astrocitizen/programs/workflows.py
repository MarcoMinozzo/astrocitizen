"""Metadados de workflow para templates P1 (AC-080/081/083/085/086)."""

from __future__ import annotations

# Esqueletos de pipeline por template PO-* (S5+)
P1_WORKFLOWS: dict[str, dict] = {
    "PO-J01": {
        "name": "Bias / dark / flat masters",
        "steps": ["acquire_calibration_frames", "build_masters", "store_versioned"],
        "networks": [],
        "analysis": "calibration",
    },
    "PO-J03": {
        "name": "Aplicar calibracao a lights",
        "steps": ["select_masters", "apply_calibration", "store_reduced"],
        "networks": [],
        "analysis": "calibration",
    },
    "PO-J05": {
        "name": "Meteo do site no plano",
        "steps": ["meteo_snapshot", "evaluate_thresholds", "annotate_blocks"],
        "networks": [],
        "analysis": "meteo",
    },
    "PO-A01": {
        "name": "Estrelas variaveis (AAVSO)",
        "steps": [
            "plan_targets",
            "acquire_lights",
            "calibrate",
            "aperture_photometry",
            "export_aavso",
        ],
        "networks": ["AAVSO"],
        "analysis": "photometry",
        "export": "aavso_extended",
    },
    "PO-A05": {
        "name": "Transitos exoplanetarios (ExoClock)",
        "steps": [
            "plan_targets",
            "acquire_lights",
            "calibrate",
            "aperture_photometry",
            "export_exoclock",
        ],
        "networks": ["ExoClock"],
        "analysis": "photometry",
        "export": "exoclock_lc",
    },
    "PO-B02": {
        "name": "Be / ARAS (monitoramento de linhas)",
        "steps": [
            "plan_targets",
            "acquire_spectrum_2d",
            "extract_spectrum_1d",
            "interpret_spectrum",
            "line_measures",
            "export_bess",
        ],
        "networks": ["ARAS", "BeSS"],
        "analysis": "spectroscopy",
        "export": "bess_fits_1d",
    },
    "PO-B03": {
        "name": "Eruptivas / novae / SN (espectro ARAS)",
        "steps": [
            "plan_targets",
            "acquire_spectrum_2d",
            "extract_spectrum_1d",
            "interpret_spectrum",
            "compare_epochs",
            "export_aras",
        ],
        "networks": ["ARAS", "TNS"],
        "analysis": "spectroscopy",
        "export": "spectrum_report",
    },
    "PO-B01": {
        "name": "Espectroscopia slit (1D + lambda)",
        "steps": [
            "plan_targets",
            "acquire_spectrum_2d",
            "calibrate",
            "extract_spectrum_1d",
            "wavelength_linear",
            "interpret_spectrum",
            "export_bess",
        ],
        "networks": ["BeSS", "ARAS"],
        "analysis": "spectroscopy",
        "export": "bess_fits_1d",
    },
    "PO-C01": {
        "name": "Astrometria asteroides / NEOs (MPC)",
        "steps": [
            "plan_targets",
            "acquire_lights",
            "calibrate",
            "plate_solve",
            "measure_astrometry",
            "export_mpc_ades",
        ],
        "networks": ["MPC"],
        "analysis": "astrometry",
        "export": "mpc_ades_psv",
    },
    "PO-C02": {
        "name": "Follow-up NEO (tracking nao-sideral)",
        "steps": [
            "plan_ephemeris",
            "acquire_nonsidereal",
            "calibrate",
            "plate_solve",
            "measure_astrometry",
            "export_mpc_ades",
        ],
        "networks": ["MPC"],
        "analysis": "astrometry",
        "export": "mpc_ades_psv",
    },
    "PO-C03": {
        "name": "Supernovas blink / TNS",
        "steps": [
            "plan_fields",
            "acquire_pair",
            "calibrate",
            "blink_diff",
            "export_tns",
        ],
        "networks": ["TNS"],
        "analysis": "blink",
        "export": "tns_at_rep",
    },
    "PO-D01": {
        "name": "Ocultacoes IOTA",
        "steps": [
            "import_prediction",
            "acquire_timed",
            "reduce_contacts",
            "export_iota_pack",
        ],
        "networks": ["IOTA"],
        "analysis": "timing",
        "export": "iota_es_pack",
    },
    "PO-E03": {
        "name": "Sol luz branca / manchas",
        "steps": [
            "safety_checklist",
            "acquire_white_light",
            "count_sunspots",
            "export_solar_report",
        ],
        "networks": ["Redes solares amadoras"],
        "analysis": "solar",
        "export": "solar_sunspot_report",
        "safety": [
            "filter_confirmed",
            "no_unfiltered_eyepiece",
            "daytime_acknowledged",
        ],
    },
    "PO-F03": {
        "name": "Log visual (diario)",
        "steps": [
            "plan_targets",
            "log_visual",
            "review_notes",
        ],
        "networks": ["diario", "AAVSO-visual"],
        "analysis": "visual_log",
        "export": "visual_log",
    },
    "PO-I01": {
        "name": "Sol radio (potencia vs tempo)",
        "steps": [
            "import_radio_series",
            "review_timeseries",
            "export_radio_csv",
        ],
        "networks": ["clubes-radio"],
        "analysis": "radio",
        "export": "radio_timeseries",
    },
    "PO-B07": {
        "name": "Echelle amador (ordens)",
        "steps": [
            "import_echelle_orders",
            "review_orders",
            "extract_spectrum_1d",
        ],
        "networks": [],
        "analysis": "echelle",
        "export": "echelle_orders",
    },
    "PO-G02": {
        "name": "Speckle interferometry",
        "steps": [
            "import_speckle_cube",
            "review_frames",
            "reduce_speckle",
        ],
        "networks": [],
        "analysis": "speckle",
        "export": "speckle_cube",
    },
    "PO-H01": {
        "name": "Polarimetria (Stokes)",
        "steps": [
            "import_polar_set",
            "estimate_stokes",
            "review_pol",
        ],
        "networks": [],
        "analysis": "polarimetry",
        "export": "polarimetry_stokes",
    },
}


def workflow_for(template_id: str) -> dict | None:
    return P1_WORKFLOWS.get(template_id)

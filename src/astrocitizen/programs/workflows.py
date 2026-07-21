"""Metadados de workflow para templates P1 (AC-080/081)."""

from __future__ import annotations

# Esqueletos de pipeline por template PO-* (S5)
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
}


def workflow_for(template_id: str) -> dict | None:
    return P1_WORKFLOWS.get(template_id)

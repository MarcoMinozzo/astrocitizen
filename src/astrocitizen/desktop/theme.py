"""Tema visual do shell desktop (ops night sky)."""

from __future__ import annotations

# Palette: deep navy + amber accent (not purple / not cream AI defaults).
COLORS = {
    "bg": "#0b1220",
    "bg_elevated": "#121a2b",
    "bg_nav": "#0e1626",
    "border": "#243049",
    "text": "#e8eef8",
    "text_muted": "#8b9bb4",
    "accent": "#d4a017",
    "accent_dim": "#9a7510",
    "ok": "#3dba7a",
    "warn": "#e0a23a",
    "bad": "#e05656",
    "input": "#182236",
}


def app_stylesheet() -> str:
    c = COLORS
    return f"""
    QWidget {{
        background-color: {c["bg"]};
        color: {c["text"]};
        font-family: "IBM Plex Sans", "Segoe UI", "Ubuntu", "Noto Sans", sans-serif;
        font-size: 13px;
    }}
    QMainWindow {{
        background-color: {c["bg"]};
    }}
    QLabel#brandTitle {{
        font-size: 18px;
        font-weight: 700;
        color: {c["text"]};
        letter-spacing: 0.5px;
    }}
    QLabel#brandSubtitle {{
        font-size: 11px;
        color: {c["text_muted"]};
    }}
    QLabel#pageTitle {{
        font-size: 16px;
        font-weight: 600;
        color: {c["text"]};
        padding: 4px 0 8px 0;
    }}
    QLabel#emptyState {{
        color: {c["text_muted"]};
        font-size: 13px;
        padding: 24px;
    }}
    QLabel#badgeOk {{
        background-color: {c["ok"]};
        color: #0b1220;
        font-weight: 700;
        padding: 4px 10px;
        border-radius: 3px;
    }}
    QLabel#badgeBad {{
        background-color: {c["bad"]};
        color: #fff;
        font-weight: 700;
        padding: 4px 10px;
        border-radius: 3px;
    }}
    QLabel#badgeIdle {{
        background-color: {c["border"]};
        color: {c["text_muted"]};
        font-weight: 600;
        padding: 4px 10px;
        border-radius: 3px;
    }}
    QListWidget#navList {{
        background-color: {c["bg_nav"]};
        border: none;
        border-right: 1px solid {c["border"]};
        outline: none;
        padding: 8px 0;
    }}
    QListWidget#navList::item {{
        padding: 10px 14px;
        margin: 2px 8px;
        border-radius: 4px;
        color: {c["text_muted"]};
    }}
    QListWidget#navList::item:selected {{
        background-color: {c["bg_elevated"]};
        color: {c["text"]};
        border-left: 3px solid {c["accent"]};
        font-weight: 600;
    }}
    QListWidget#navList::item:hover {{
        background-color: {c["input"]};
        color: {c["text"]};
    }}
    QPushButton {{
        background-color: {c["accent"]};
        color: #0b1220;
        border: none;
        border-radius: 4px;
        padding: 7px 14px;
        font-weight: 600;
    }}
    QPushButton:hover {{
        background-color: {c["warn"]};
    }}
    QPushButton:disabled {{
        background-color: {c["border"]};
        color: {c["text_muted"]};
    }}
    QPushButton#secondaryBtn {{
        background-color: {c["input"]};
        color: {c["text"]};
        border: 1px solid {c["border"]};
    }}
    QPushButton#secondaryBtn:hover {{
        border-color: {c["accent"]};
        color: {c["accent"]};
        background-color: {c["bg_elevated"]};
    }}
    QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit, QTextEdit, QPlainTextEdit {{
        background-color: {c["input"]};
        border: 1px solid {c["border"]};
        border-radius: 4px;
        padding: 5px 8px;
        selection-background-color: {c["accent_dim"]};
    }}
    QComboBox::drop-down {{
        border: none;
        width: 20px;
    }}
    QTableWidget {{
        background-color: {c["bg_elevated"]};
        alternate-background-color: {c["bg"]};
        gridline-color: {c["border"]};
        border: 1px solid {c["border"]};
        border-radius: 4px;
    }}
    QHeaderView::section {{
        background-color: {c["bg_nav"]};
        color: {c["text_muted"]};
        padding: 6px 8px;
        border: none;
        border-bottom: 1px solid {c["border"]};
        font-weight: 600;
    }}
    QTabWidget::pane {{
        border: 1px solid {c["border"]};
        background: {c["bg_elevated"]};
        border-radius: 4px;
    }}
    QTabBar::tab {{
        background: {c["bg_nav"]};
        color: {c["text_muted"]};
        padding: 8px 14px;
        border: 1px solid {c["border"]};
        border-bottom: none;
        margin-right: 2px;
    }}
    QTabBar::tab:selected {{
        background: {c["bg_elevated"]};
        color: {c["accent"]};
        font-weight: 600;
    }}
    QStatusBar {{
        background: {c["bg_nav"]};
        color: {c["text_muted"]};
        border-top: 1px solid {c["border"]};
    }}
    QSplitter::handle {{
        background: {c["border"]};
        width: 2px;
    }}
    QScrollBar:vertical {{
        background: {c["bg"]};
        width: 10px;
        margin: 0;
    }}
    QScrollBar::handle:vertical {{
        background: {c["border"]};
        border-radius: 4px;
        min-height: 24px;
    }}
    QLabel#radarPane {{
        background-color: #060a12;
        color: {c["text_muted"]};
        border: 1px solid {c["border"]};
        border-radius: 4px;
    }}
    """


def viability_badge(ok: bool | None) -> tuple[str, str]:
    """Return (label, objectName) for night viability badge."""
    if ok is True:
        return "VIABLE", "badgeOk"
    if ok is False:
        return "INVIABLE", "badgeBad"
    return "-", "badgeIdle"


def empty_state_text(module: str) -> str:
    hints = {
        "Sites": "Nenhum site. Use Novo na pagina Sites, ou CLI: astrocitizen site add",
        "Equipamento": "Nenhum equipamento. Use Novo na pagina Equipamento.",
        "Programas": "Nenhum programa. Use Novo na pagina Programas, ou CLI.",
        "Alvos": "Nenhum alvo. Use Novo na pagina Alvos, ou CLI: astrocitizen target add",
        "Plano diario": "Nenhum plano. Use Noite -> Gerar plano.",
        "Sessao": "Nenhuma sessao registada.",
        "Arquivo": "Nenhuma observacao no arquivo.",
    }
    return hints.get(module, "Sem dados.")


def apply_theme(app: object) -> None:
    """Apply stylesheet to QApplication."""
    set_style = getattr(app, "setStyleSheet", None)
    if callable(set_style):
        set_style(app_stylesheet())

"""AAVSO portal URLs e allowlist (AC-095 / AC-096).

Campanhas: sem API publica (browser). Submissao: AEF + WebObs oficial.
"""

from __future__ import annotations

import re
from urllib.parse import urlparse

AAVSO_CAMPAIGNS_HOME = "https://apps.aavso.org/v2/campaigns/search"
AAVSO_CAMPAIGN_DETAIL_TMPL = "https://apps.aavso.org/v2/campaigns/{campaign_id}"
WEBOBS_URL = "https://www.aavso.org/webobs/"
VSX_OBJECT_API = (
    "https://www.aavso.org/vsx/index.php?view=api.object&ident={ident}&format=json"
)

_CAMPAIGN_ID_RE = re.compile(
    r"^/v2/campaigns/(?P<id>\d+)/?$",
    re.IGNORECASE,
)


def is_aavso_host(url: str) -> bool:
    """True se o host for aavso.org ou subdominio (apps., www., …)."""
    try:
        host = (urlparse(url).hostname or "").lower()
    except ValueError:
        return False
    return host == "aavso.org" or host.endswith(".aavso.org")


def campaign_id_from_url(url: str) -> str | None:
    """Extrai id numerico de …/v2/campaigns/{id}."""
    try:
        path = urlparse(url).path or ""
    except ValueError:
        return None
    m = _CAMPAIGN_ID_RE.match(path)
    return m.group("id") if m else None


def campaign_status_label(url: str) -> str:
    """Texto curto para status bar."""
    cid = campaign_id_from_url(url)
    if cid:
        return f"Campanha {cid}"
    if is_aavso_host(url):
        return "AAVSO"
    return ""

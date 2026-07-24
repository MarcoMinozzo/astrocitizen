"""Resolver CDS Sesame — nome → coords ICRS (AC-211)."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from astrocitizen.shared.errors import DomainError, NotFoundError

_DEFAULT_TIMEOUT_S = 30.0
_SESAME_BASE = "https://cds.unistra.fr/cgi-bin/nph-sesame/-oxp/SNV"


def _local_tag(tag: str) -> str:
    if "}" in tag:
        return tag.rsplit("}", 1)[-1]
    return tag


def _text(el: ET.Element | None) -> str | None:
    if el is None or el.text is None:
        return None
    t = el.text.strip()
    return t or None


def parse_sesame_xml(raw: str, *, query: str) -> dict[str, Any]:
    """Parse resposta Sesame (-oxp) → ra_deg/dec_deg + external_ids."""
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as exc:
        raise DomainError("Sesame devolveu XML invalido", rule_id="AC-211") from exc

    for target in root.iter():
        if _local_tag(target.tag) != "Target":
            continue
        for resolver in target:
            if _local_tag(resolver.tag) != "Resolver":
                continue
            jra = None
            jde = None
            otype = None
            alias = None
            for child in resolver:
                name = _local_tag(child.tag)
                if name == "jradeg":
                    try:
                        jra = float((_text(child) or "").strip())
                    except ValueError:
                        jra = None
                elif name == "jdedeg":
                    try:
                        jde = float((_text(child) or "").strip())
                    except ValueError:
                        jde = None
                elif name == "otype":
                    otype = _text(child)
                elif name == "alias" and alias is None:
                    alias = _text(child)
            if jra is None or jde is None:
                continue
            designation = (
                target.attrib.get("name")
                or alias
                or query
            ).strip()
            external_ids: dict[str, Any] = {"sesame": designation, "source": "sesame"}
            resolver_name = (resolver.attrib.get("name") or "").strip()
            if resolver_name:
                external_ids["sesame_resolver"] = resolver_name
            if otype:
                external_ids["otype"] = otype
            return {
                "ra_deg": jra,
                "dec_deg": jde,
                "designation": designation,
                "external_ids": external_ids,
            }

    raise NotFoundError(f"Sesame nao encontrou: {query}")


class SesameResolver:
    """Resolve designacao via CDS Sesame HTTP-GET (Simbad+NED+VizieR)."""

    def __init__(
        self,
        *,
        timeout_s: float = _DEFAULT_TIMEOUT_S,
        opener: Any | None = None,
        base_url: str = _SESAME_BASE,
    ) -> None:
        self.timeout_s = timeout_s
        self._opener = opener
        self.base_url = base_url.rstrip("?")

    def resolve(self, name: str) -> dict[str, Any]:
        ident = (name or "").strip()
        if not ident:
            raise DomainError("nome Sesame vazio", rule_id="AC-211")
        url = f"{self.base_url}?{quote(ident)}"
        raw = self._fetch(url)
        return parse_sesame_xml(raw, query=ident)

    def _fetch(self, url: str) -> str:
        if self._opener is not None:
            return self._opener(url)
        req = Request(url, headers={"User-Agent": "AstroCitizen/0.0.1 (Sesame)"})
        try:
            with urlopen(req, timeout=self.timeout_s) as resp:  # noqa: S310
                return resp.read().decode("utf-8", errors="replace")
        except HTTPError as exc:
            if exc.code == 404:
                raise NotFoundError(f"Sesame HTTP 404: {url}") from exc
            raise DomainError(f"Sesame HTTP {exc.code}", rule_id="AC-211") from exc
        except URLError as exc:
            raise DomainError(
                f"Sesame rede indisponivel: {exc.reason}", rule_id="AC-211"
            ) from exc

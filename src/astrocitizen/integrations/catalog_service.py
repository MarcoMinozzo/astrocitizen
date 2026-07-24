"""CatalogResolveService — resolve + cache + enrich targets (AC-226)."""

from __future__ import annotations

from typing import Any, Iterable, Sequence
from uuid import UUID

from astrocitizen.integrations.registry import ProviderRegistry, default_providers
from astrocitizen.planning.models import Target
from astrocitizen.shared.errors import DomainError, NotFoundError
from astrocitizen.shared.timeutil import utc_now_iso

DEFAULT_PROVIDERS: tuple[str, ...] = ("sesame", "vsx", "simbad", "vizier", "gaia")
_NEAR_PROVIDERS: frozenset[str] = frozenset({"vizier", "gaia"})


def _merge_payload(base: dict[str, Any], incoming: dict[str, Any], source: str) -> dict[str, Any]:
    out = dict(base)
    sources = list(out.get("sources") or [])
    if source not in sources:
        sources.append(source)
    out["sources"] = sources

    if out.get("ra_deg") is None and incoming.get("ra_deg") is not None:
        out["ra_deg"] = float(incoming["ra_deg"])
    if out.get("dec_deg") is None and incoming.get("dec_deg") is not None:
        out["dec_deg"] = float(incoming["dec_deg"])

    # Designação: preferir nome humano; nunca trocar por source_id Gaia numérico
    # nem por labels de cone (viz/gaia).
    desig = incoming.get("designation")
    if desig:
        cur = str(out.get("designation") or "").strip()
        new = str(desig).strip()
        if not cur:
            out["designation"] = new
        elif _is_numeric_id(cur) and not _is_numeric_id(new):
            out["designation"] = new
        elif not _is_numeric_id(cur) and _is_numeric_id(new):
            pass
        elif source in ("sesame", "simbad", "harris") and not _is_numeric_id(new):
            q = str(out.get("query") or "").strip()
            if cur == q or _is_numeric_id(cur):
                out["designation"] = new

    ids = dict(out.get("external_ids") or {})
    in_ids = dict(incoming.get("external_ids") or {})
    stellar_near = source in ("gaia", "vizier")
    skip_generic = {"mag_max", "mag_min"} if stellar_near else set()
    for k, v in in_ids.items():
        if v is None or k in skip_generic:
            continue
        if k not in ids or ids[k] in (None, ""):
            ids[k] = v

    # Campos preferidos por fonte — Gaia/VizieR NÃO definem mag_max (estrela ≠ objecto)
    preferred: tuple[str, ...]
    if source == "vsx":
        preferred = (
            "auid",
            "variability_type",
            "period",
            "mag_max",
            "mag_min",
            "vsx",
        )
    elif source in ("sesame", "simbad"):
        preferred = (
            "otype",
            "simbad",
            "sesame",
            "vmag",
            "bmag",
            "rmag",
            "imag",
            "umag",
            "band_notes",
            "mag_max",
        )
    elif source == "harris":
        preferred = ("vmag", "mag_max", "band_notes", "harris", "otype")
    elif stellar_near:
        preferred = (
            "gmag",
            "gaia_source_id",
            "parallax_mas",
            "pmra",
            "pmdec",
            "vizier",
            "gaia",
        )
    else:
        preferred = (
            "auid",
            "variability_type",
            "period",
            "mag_max",
            "mag_min",
            "vsx",
            "otype",
            "vmag",
            "gmag",
            "gaia_source_id",
            "parallax_mas",
            "pmra",
            "pmdec",
        )
    for k in preferred:
        if k in in_ids and in_ids[k] is not None:
            ids[k] = in_ids[k]

    # mag_max: VSX ou V integrada (Harris/SIMBAD); nunca G de estrela próxima
    if "mag_max" in in_ids and in_ids["mag_max"] is not None and not stellar_near:
        ids["mag_max"] = in_ids["mag_max"]
    if "mag_min" in in_ids and in_ids["mag_min"] is not None and source == "vsx":
        ids["mag_min"] = in_ids["mag_min"]
    if ids.get("mag_max") is None and ids.get("vmag") is not None:
        ids["mag_max"] = ids["vmag"]

    out["external_ids"] = ids
    return out


def _is_numeric_id(value: str) -> bool:
    s = (value or "").strip()
    return bool(s) and s.isdigit()


# Objectos extensos: cone Gaia/VizieR apanha estrela, não a fotometria integrada
_EXTENDED_OTYPE_PREFIXES: tuple[str, ...] = (
    "GlC",
    "GCl",
    "OpC",
    "Cl*",
    "As*",
    "C?*",
    "Galaxy",
    "G",
    "GiC",
    "GiG",
    "IG",
    "PaG",
    "QSO",
    "AGN",
    "Rad",
    "HII",
    "PN",
    "SNR",
    "Neb",
    "EmN",
    "CGb",
    "MoC",
    "dark",
    "ISM",
    "SFR",
    "bubble",
    "mul",
    "PoC",
    "SBG",
    "LSB",
    "bCG",
    "EmG",
    "SyG",
    "rG",
    "BiC",
    "GrG",
    "CGG",
    "ClG",
    "SuperClG",
    "PartofG",
    "BlueCompG",
    "GinCl",
    "GinGroup",
)


def _is_extended_object(external_ids: dict[str, Any] | None) -> bool:
    otype = str((external_ids or {}).get("otype") or "").strip()
    if not otype:
        return False
    if otype in _EXTENDED_OTYPE_PREFIXES:
        return True
    # SIMBAD compact codes: GlC, OpC, ...
    return any(otype.startswith(p) for p in ("GlC", "GCl", "OpC", "Cl*", "Galaxy", "G "))


def catalog_notes_from_ids(external_ids: dict[str, Any] | None) -> str:
    """Notas curtas para ObservationBlock a partir de IDs de catálogo."""
    ids = external_ids or {}
    parts: list[str] = []
    vsx_type = ids.get("variability_type") or ids.get("vsx_type")
    if vsx_type:
        parts.append(f"vsx_type={vsx_type}")
    mag = ids.get("mag_max")
    if mag is not None:
        parts.append(f"mag_max={mag}")
    elif ids.get("gmag") is not None:
        parts.append(f"gmag={ids['gmag']}")
    period = ids.get("period")
    if period is not None:
        parts.append(f"period={period}")
    otype = ids.get("otype")
    if otype and not vsx_type:
        parts.append(f"otype={otype}")
    sid = ids.get("gaia_source_id")
    if sid:
        parts.append(f"gaia={sid}")
    return "; ".join(parts)


def mag_max_from_ids(external_ids: dict[str, Any] | None) -> float | None:
    ids = external_ids or {}
    raw = ids.get("mag_max")
    if raw is None:
        return None
    try:
        return float(raw)
    except (TypeError, ValueError):
        return None


class CatalogResolveService:
    """Facade: Sesame → VSX → SIMBAD, com institutional_cache e enrich Target."""

    def __init__(
        self,
        archive: Any,
        registry: ProviderRegistry | None = None,
    ) -> None:
        self.archive = archive
        self.registry = registry or ProviderRegistry(
            default_providers(archive=archive)
        )

    def _cache_get(self, provider: str, object_id: str) -> dict[str, Any] | None:
        row = self.archive.get_institutional_cache(
            provider=provider, object_id=object_id
        )
        if row is None:
            return None
        payload = row.get("payload")
        return payload if isinstance(payload, dict) else None

    def _cache_keys_for_target(self, target: Target) -> list[str]:
        keys: list[str] = []
        for cand in (
            target.designation,
            (target.external_ids or {}).get("auid"),
            (target.external_ids or {}).get("vsx"),
            (target.external_ids or {}).get("sesame"),
            (target.external_ids or {}).get("simbad"),
        ):
            s = str(cand or "").strip()
            if s and s not in keys:
                keys.append(s)
        return keys

    def resolve(
        self,
        name: str,
        *,
        providers: Sequence[str] = DEFAULT_PROVIDERS,
        use_cache: bool = True,
        network: bool = True,
    ) -> dict[str, Any]:
        query = (name or "").strip()
        if not query:
            raise NotFoundError("nome de catalogo vazio")

        merged: dict[str, Any] = {
            "query": query,
            "designation": query,
            "ra_deg": None,
            "dec_deg": None,
            "external_ids": {},
            "sources": [],
        }

        for provider_name in providers:
            # Gaia/VizieR (estrelas) nao fazem sentido como fonte primaria de GlC/Galaxy
            if provider_name in _NEAR_PROVIDERS and _is_extended_object(
                merged.get("external_ids")
            ):
                continue
            payload: dict[str, Any] | None = None
            from_network = False
            if use_cache:
                payload = self._cache_get(provider_name, query)
                # Cache antigo pode ter G de estrela como mag_max — ignorar
                if (
                    payload is not None
                    and provider_name in _NEAR_PROVIDERS
                    and _is_extended_object(merged.get("external_ids"))
                ):
                    payload = None
            if payload is None and network:
                try:
                    provider = self.registry.get(provider_name)
                    if not provider.supports("search"):
                        continue
                    # Gaia por nome livre falha — enriquecer por cone depois
                    if provider_name in _NEAR_PROVIDERS and provider_name == "gaia":
                        if not str(query).strip().isdigit():
                            continue
                    payload = provider.search_object(query)
                    from_network = True
                except (NotFoundError, DomainError):
                    # Provider miss / rede — tentar seguinte
                    payload = None
            if payload is None:
                continue
            # Backup: garantir cache se o provider nao gravou
            if from_network and self.archive is not None:
                object_id = str(
                    (payload.get("external_ids") or {}).get(provider_name)
                    or payload.get("designation")
                    or query
                ).strip()
                self.archive.upsert_institutional_cache(
                    provider=provider_name,
                    object_id=object_id,
                    payload=payload,
                    fetched_at=utc_now_iso(),
                )
                if query != object_id:
                    self.archive.upsert_institutional_cache(
                        provider=provider_name,
                        object_id=query,
                        payload=payload,
                        fetched_at=utc_now_iso(),
                    )
            merged = _merge_payload(merged, payload, provider_name)

        # Cone enrich (VizieR/Gaia) — só para fontes pontuais; enxames/galáxias
        # não devem herdar G de uma estrela aleatória no cone.
        if (
            network
            and merged.get("ra_deg") is not None
            and merged.get("dec_deg") is not None
            and not _is_extended_object(merged.get("external_ids"))
        ):
            ra = float(merged["ra_deg"])
            dec = float(merged["dec_deg"])
            for provider_name in providers:
                if provider_name not in _NEAR_PROVIDERS:
                    continue
                if provider_name in (merged.get("sources") or []):
                    continue
                try:
                    provider = self.registry.get(provider_name)
                    near = getattr(provider, "search_near", None)
                    if not callable(near):
                        continue
                    payload = near(ra, dec)
                    merged = _merge_payload(merged, payload, provider_name)
                except (NotFoundError, DomainError):
                    continue

        # Fotometria integrada (Harris) para enxames globulares
        if network:
            otype = str((merged.get("external_ids") or {}).get("otype") or "")
            if otype.startswith("GlC") or otype.startswith("GCl"):
                merged = self._enrich_harris_globular(merged, query=query)

        # SIMBAD TAP fotometria se ainda faltar V/B/R (galáxias, etc.)
        if network and "simbad" in providers:
            merged = self._enrich_simbad_photometry(merged, query=query)

        if merged.get("ra_deg") is None or merged.get("dec_deg") is None:
            raise NotFoundError(f"catalogo nao resolveu coords: {query}")
        return merged

    def _enrich_simbad_photometry(
        self, merged: dict[str, Any], *, query: str
    ) -> dict[str, Any]:
        """Completa vmag/bmag/rmag via SIMBAD TAP allfluxes (AC-236)."""
        ids = dict(merged.get("external_ids") or {})
        # VSX ja definiu amplitude — nao sobrescrever mag_max/min
        if ids.get("variability_type") or ids.get("vsx"):
            if ids.get("vmag") is not None or ids.get("bmag") is not None:
                return merged
        if ids.get("vmag") is not None and ids.get("bmag") is not None:
            return merged
        try:
            from astrocitizen.adapters.sky.simbad_tap import SimbadTapResolver

            payload = SimbadTapResolver(timeout_s=25.0).resolve(query)
        except (NotFoundError, DomainError):
            return merged
        # Nao deixar TAP apagar mag_max VSX
        if ids.get("variability_type") or ids.get("vsx"):
            in_ids = dict(payload.get("external_ids") or {})
            in_ids.pop("mag_max", None)
            in_ids.pop("mag_min", None)
            payload = dict(payload)
            payload["external_ids"] = in_ids
        return _merge_payload(merged, payload, "simbad")

    def _enrich_harris_globular(
        self, merged: dict[str, Any], *, query: str
    ) -> dict[str, Any]:
        """VII/202 Harris — Vt integrada para GlC (ex. M56 ≈ 8.3)."""
        ids = dict(merged.get("external_ids") or {})
        # Nao sobrescrever fotometria VSX de variaveis
        if ids.get("variability_type") or ids.get("vsx"):
            return merged
        try:
            from astrocitizen.adapters.sky.vizier_resolver import VizierResolver

            resolver = VizierResolver(source="VII/202/catalog", timeout_s=20.0)
            payload = resolver.resolve(query)
        except (NotFoundError, DomainError):
            return merged
        return _merge_payload(merged, payload, "harris")

    def resolve_from_cache(
        self,
        name: str,
        *,
        providers: Sequence[str] = DEFAULT_PROVIDERS,
        extra_keys: Iterable[str] | None = None,
    ) -> dict[str, Any] | None:
        """Junta hits de cache sem rede. None se nao houver coords."""
        keys: list[str] = []
        for cand in (name, *(extra_keys or ())):
            s = str(cand or "").strip()
            if s and s not in keys:
                keys.append(s)
        if not keys:
            return None

        merged: dict[str, Any] = {
            "query": keys[0],
            "designation": keys[0],
            "ra_deg": None,
            "dec_deg": None,
            "external_ids": {},
            "sources": [],
        }
        any_hit = False
        for provider_name in providers:
            for key in keys:
                payload = self._cache_get(provider_name, key)
                if payload is None:
                    continue
                any_hit = True
                merged = _merge_payload(merged, payload, provider_name)
                break
        if not any_hit:
            return None
        if merged.get("ra_deg") is None or merged.get("dec_deg") is None:
            # Cache parcial (ex. so mag) — devolver mesmo assim para notes
            return merged
        return merged

    def enrich_target(
        self,
        target: Target,
        *,
        network: bool = False,
        providers: Sequence[str] = DEFAULT_PROVIDERS,
    ) -> Target:
        """Actualiza ra/dec/external_ids a partir do cache (ou resolve com rede)."""
        keys = self._cache_keys_for_target(target)
        resolved: dict[str, Any] | None
        if network:
            try:
                resolved = self.resolve(
                    target.designation,
                    providers=providers,
                    use_cache=True,
                    network=True,
                )
            except NotFoundError:
                resolved = self.resolve_from_cache(
                    target.designation,
                    providers=providers,
                    extra_keys=keys[1:],
                )
        else:
            resolved = self.resolve_from_cache(
                target.designation,
                providers=providers,
                extra_keys=keys[1:],
            )

        if resolved is None:
            return target

        if resolved.get("ra_deg") is not None:
            target.ra_deg = float(resolved["ra_deg"])
        if resolved.get("dec_deg") is not None:
            target.dec_deg = float(resolved["dec_deg"])

        ids = dict(target.external_ids or {})
        for k, v in dict(resolved.get("external_ids") or {}).items():
            if v is not None:
                ids[k] = v
        target.external_ids = ids

        desig = resolved.get("designation")
        if desig and isinstance(desig, str) and desig.strip():
            # Nao renomear se o utilizador ja tem designation propria distinta
            if not target.designation or target.designation.strip() == keys[0]:
                target.designation = desig.strip()

        saved = self.archive.upsert_target(target)
        # Buffer do catálogo próprio (AC-235): toda busca actualiza a ficha
        try:
            from astrocitizen.catalog.dossier import CatalogDossierService

            CatalogDossierService(self.archive, resolve_service=self).persist_resolved(
                target.workspace_id,
                target.designation,
                resolved,
                enqueue_sync=True,
            )
        except Exception:
            pass
        return saved

    def refresh_program_targets(
        self,
        workspace_id: UUID,
        *,
        providers: Sequence[str] = DEFAULT_PROVIDERS,
    ) -> list[Target]:
        """Resolve (rede+cache) todos os alvos ligados a programas active."""
        programs = self.archive.list_programs(workspace_id, state="active")
        seen: set[UUID] = set()
        updated: list[Target] = []
        for program in programs:
            for target, _role, _so in self.archive.list_program_targets(program.id):
                if target.id in seen:
                    continue
                seen.add(target.id)
                try:
                    enriched = self.enrich_target(
                        target, network=True, providers=providers
                    )
                    updated.append(enriched)
                except NotFoundError:
                    continue
        return updated

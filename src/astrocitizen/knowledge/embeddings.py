"""Embeddings locais leves para KB (AC-195) — D-010, sem torch no core."""

from __future__ import annotations

import hashlib
import math
import re
import struct
from typing import Protocol, runtime_checkable

from astrocitizen.knowledge.search import fold_corrupt_accents

_TOKEN_RE = re.compile(r"[a-z0-9]+", re.IGNORECASE)

# Dimensao fixa pequena: ~1.5 KiB/chunk; suficiente para corpus T3 MVP
DEFAULT_DIM = 384
DEFAULT_MODEL_ID = "hashing-ngram-v1"


@runtime_checkable
class EmbedderPort(Protocol):
    """Gera vectores densos locais (opt-in; FTS continua a funcionar sem isto)."""

    @property
    def model_id(self) -> str: ...

    @property
    def dim(self) -> int: ...

    def embed(self, text: str) -> list[float]: ...


class HashingNgramEmbedder:
    """Bag-of-hashed char/word n-grams → vector L2-normalizado (stdlib only)."""

    def __init__(self, *, dim: int = DEFAULT_DIM, model_id: str = DEFAULT_MODEL_ID) -> None:
        if dim < 32:
            raise ValueError("dim demasiado baixo")
        self._dim = int(dim)
        self._model_id = model_id

    @property
    def model_id(self) -> str:
        return self._model_id

    @property
    def dim(self) -> int:
        return self._dim

    def embed(self, text: str) -> list[float]:
        folded = fold_corrupt_accents(text or "").lower()
        vec = [0.0] * self._dim
        tokens = _TOKEN_RE.findall(folded)
        # word unigrams + bigrams
        feats: list[str] = list(tokens)
        for i in range(len(tokens) - 1):
            feats.append(f"{tokens[i]}_{tokens[i + 1]}")
        # char trigrams on compact text (recall para typos / acentos perdidos)
        compact = re.sub(r"\s+", "", folded)
        for i in range(max(0, len(compact) - 2)):
            feats.append(f"c:{compact[i : i + 3]}")
        for feat in feats:
            h = hashlib.blake2b(feat.encode("utf-8"), digest_size=8).digest()
            idx = int.from_bytes(h[:4], "little") % self._dim
            sign = 1.0 if (h[4] & 1) == 0 else -1.0
            vec[idx] += sign
        return _l2_normalize(vec)


def pack_vector(vec: list[float]) -> bytes:
    return struct.pack(f"<{len(vec)}f", *vec)


def unpack_vector(blob: bytes, dim: int) -> list[float]:
    n = dim
    expected = n * 4
    if len(blob) != expected:
        raise ValueError(f"vector blob size {len(blob)} != {expected}")
    return list(struct.unpack(f"<{n}f", blob))


def cosine_similarity(a: list[float], b: list[float]) -> float:
    if len(a) != len(b) or not a:
        return 0.0
    return sum(x * y for x, y in zip(a, b, strict=True))


def rrf_fuse(
    ranked_lists: list[list[str]],
    *,
    k: int = 60,
    limit: int = 10,
) -> list[tuple[str, float]]:
    """Reciprocal Rank Fusion — devolve (id, score) ordenado desc."""
    scores: dict[str, float] = {}
    for ranked in ranked_lists:
        for rank, doc_id in enumerate(ranked, start=1):
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank)
    ordered = sorted(scores.items(), key=lambda kv: (-kv[1], kv[0]))
    return ordered[: max(1, limit)]


def _l2_normalize(vec: list[float]) -> list[float]:
    norm = math.sqrt(sum(v * v for v in vec))
    if norm <= 0.0:
        return vec
    return [v / norm for v in vec]


def default_embedder() -> HashingNgramEmbedder:
    return HashingNgramEmbedder()

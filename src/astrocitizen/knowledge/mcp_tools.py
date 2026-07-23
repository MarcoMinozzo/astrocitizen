"""Tools MCP read-only da KB (AC-197) — contrato tipo Vectron."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any, Callable

from astrocitizen.adapters.sqlite.hybrid_retriever import HybridRetriever
from astrocitizen.ports.retriever import RetrieveFilters

TOOL_KB_SEARCH = "kb_search"
TOOL_KB_GET_CHUNK = "kb_get_chunk"
TOOL_KB_LIST_SOURCES = "kb_list_sources"

TOOL_DEFS: list[dict[str, Any]] = [
    {
        "name": TOOL_KB_SEARCH,
        "description": (
            "Pesquisa lexical/hibrida na base de conhecimento AstroCitizen. "
            "Devolve citacoes com chunk_id, source_id e trust_tier."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "limit": {"type": "integer", "default": 5, "minimum": 1, "maximum": 20},
                "mode": {
                    "type": "string",
                    "enum": ["fts", "vector", "hybrid"],
                    "default": "hybrid",
                },
                "trust_tier": {"type": "string"},
                "source_id": {"type": "string"},
                "lang": {"type": "string"},
                "po_id": {"type": "string"},
                "network": {"type": "string"},
                "topic": {"type": "string"},
            },
            "required": ["query"],
        },
    },
    {
        "name": TOOL_KB_GET_CHUNK,
        "description": "Obtem um chunk completo por chunk_id (corpo + metadados de citacao).",
        "inputSchema": {
            "type": "object",
            "properties": {"chunk_id": {"type": "string"}},
            "required": ["chunk_id"],
        },
    },
    {
        "name": TOOL_KB_LIST_SOURCES,
        "description": "Lista fontes ingeridas (source_id, title, trust_tier, topics).",
        "inputSchema": {
            "type": "object",
            "properties": {"trust_tier": {"type": "string"}},
        },
    },
]


@dataclass
class RateLimiter:
    """Rate limit simples por processo (chamadas / janela)."""

    max_calls: int = 60
    window_s: float = 60.0
    _times: list[float] = field(default_factory=list)

    def allow(self) -> bool:
        now = time.monotonic()
        cutoff = now - self.window_s
        self._times = [t for t in self._times if t >= cutoff]
        if len(self._times) >= self.max_calls:
            return False
        self._times.append(now)
        return True


@dataclass
class KbMcpServer:
    """Dispatcher de tools read-only sobre HybridRetriever."""

    retriever: HybridRetriever
    rate_limiter: RateLimiter = field(default_factory=RateLimiter)

    def list_tools(self) -> list[dict[str, Any]]:
        return list(TOOL_DEFS)

    def call_tool(self, name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
        if not self.rate_limiter.allow():
            return {
                "ok": False,
                "error": "rate_limited",
                "message": "Too many KB tool calls; try again later.",
            }
        args = dict(arguments or {})
        handlers: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {
            TOOL_KB_SEARCH: self._kb_search,
            TOOL_KB_GET_CHUNK: self._kb_get_chunk,
            TOOL_KB_LIST_SOURCES: self._kb_list_sources,
        }
        handler = handlers.get(name)
        if handler is None:
            return {"ok": False, "error": "unknown_tool", "message": f"Unknown tool: {name}"}
        try:
            return handler(args)
        except Exception as exc:  # noqa: BLE001 — boundary MCP
            return {"ok": False, "error": "tool_error", "message": str(exc)}

    def _kb_search(self, args: dict[str, Any]) -> dict[str, Any]:
        query = str(args.get("query") or "").strip()
        if not query:
            return {"ok": False, "error": "invalid_args", "message": "query required"}
        limit = int(args.get("limit") or 5)
        mode = str(args.get("mode") or "hybrid")
        filters = RetrieveFilters(
            trust_tier=args.get("trust_tier"),
            source_id=args.get("source_id"),
            lang=args.get("lang"),
            po_id=args.get("po_id"),
            network=args.get("network"),
            topic=args.get("topic"),
        )
        hits = self.retriever.search(query, limit=limit, filters=filters, mode=mode)  # type: ignore[arg-type]
        return {
            "ok": True,
            "hits": [
                {
                    "chunk_id": h.chunk_id,
                    "source_id": h.source_id,
                    "trust_tier": h.trust_tier,
                    "title": h.title,
                    "snippet": h.snippet,
                    "score": h.score,
                    "path": h.path,
                    "lang": h.lang,
                    "po_id": h.po_id,
                    "network": h.network,
                    "topics": list(h.topics or []),
                    "citation": h.citation_label(),
                }
                for h in hits
            ],
        }

    def _kb_get_chunk(self, args: dict[str, Any]) -> dict[str, Any]:
        chunk_id = str(args.get("chunk_id") or "").strip()
        if not chunk_id:
            return {"ok": False, "error": "invalid_args", "message": "chunk_id required"}
        cite = self.retriever.get_chunk(chunk_id)
        if cite is None:
            return {"ok": False, "error": "not_found", "message": chunk_id}
        return {
            "ok": True,
            "chunk": {
                "chunk_id": cite.chunk_id,
                "source_id": cite.source_id,
                "trust_tier": cite.trust_tier,
                "title": cite.title,
                "path": cite.path,
                "lang": cite.lang,
                "po_id": cite.po_id,
                "network": cite.network,
                "topics": list(cite.topics or []),
                "chunk_hash": cite.chunk_hash,
                "body": cite.body,
                "citation": cite.citation_label(),
            },
        }

    def _kb_list_sources(self, args: dict[str, Any]) -> dict[str, Any]:
        sources = self.retriever.list_sources(trust_tier=args.get("trust_tier"))
        return {"ok": True, "sources": sources}


def handle_mcp_jsonrpc(server: KbMcpServer, message: dict[str, Any]) -> dict[str, Any] | None:
    """Subset MCP/JSON-RPC (initialize, tools/list, tools/call, ping)."""
    method = message.get("method")
    msg_id = message.get("id")
    params = message.get("params") or {}

    def _result(result: Any) -> dict[str, Any]:
        return {"jsonrpc": "2.0", "id": msg_id, "result": result}

    def _error(code: int, err_msg: str) -> dict[str, Any]:
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "error": {"code": code, "message": err_msg},
        }

    if method == "initialize":
        return _result(
            {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "astrocitizen-kb", "version": "0.1.0"},
            }
        )
    if method == "notifications/initialized":
        return None
    if method == "ping":
        return _result({})
    if method == "tools/list":
        return _result({"tools": server.list_tools()})
    if method == "tools/call":
        name = str(params.get("name") or "")
        arguments = params.get("arguments") or {}
        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments)
            except json.JSONDecodeError:
                return _error(-32602, "arguments must be object or JSON string")
        if not isinstance(arguments, dict):
            return _error(-32602, "arguments must be object")
        payload = server.call_tool(name, arguments)
        text = json.dumps(payload, ensure_ascii=False, indent=2)
        return _result(
            {
                "content": [{"type": "text", "text": text}],
                "isError": not bool(payload.get("ok", False)),
            }
        )
    if method == "shutdown":
        return _result({})
    return _error(-32601, f"Method not found: {method}")

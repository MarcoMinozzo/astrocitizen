"""AC-197: MCP read-only KB tools."""

from __future__ import annotations

from pathlib import Path

from astrocitizen.adapters.sqlite import HybridRetriever, SqliteArchive
from astrocitizen.knowledge.mcp_tools import (
    TOOL_KB_GET_CHUNK,
    TOOL_KB_GET_GLOSSARY,
    TOOL_KB_LIST_SOURCES,
    TOOL_KB_SEARCH,
    KbMcpServer,
    RateLimiter,
    handle_mcp_jsonrpc,
)
from astrocitizen.knowledge.models import KnowledgeChunk, KnowledgeDocument


def _seed(archive: SqliteArchive) -> None:
    archive.upsert_knowledge_document(
        KnowledgeDocument(
            id="docs-analise-espectral",
            source_id="docs-analise-espectral",
            path="docs/ANALISE.md",
            title="Analise",
            trust_tier="T3",
            lang="pt",
            topics=["spectrum"],
            status="ingested",
        )
    )
    archive.upsert_knowledge_chunk(
        KnowledgeChunk(
            id="docs-analise-espectral-001",
            document_id="docs-analise-espectral",
            source_id="docs-analise-espectral",
            body="AC-106 spectrum-report interpretacao assistida deterministica.",
            trust_tier="T3",
            chunk_hash="sha256:x",
            title="AC-106",
            lang="pt",
            topics=["spectrum"],
        )
    )
    archive.rebuild_knowledge_fts()


def test_mcp_tools_search_get_list(tmp_path: Path) -> None:
    archive = SqliteArchive(tmp_path / "m.sqlite3")
    archive.migrate()
    _seed(archive)
    server = KbMcpServer(HybridRetriever(archive))
    names = {t["name"] for t in server.list_tools()}
    assert names == {
        TOOL_KB_SEARCH,
        TOOL_KB_GET_CHUNK,
        TOOL_KB_LIST_SOURCES,
        TOOL_KB_GET_GLOSSARY,
    }

    search = server.call_tool(TOOL_KB_SEARCH, {"query": "AC-106 spectrum", "limit": 3})
    assert search["ok"]
    assert search["hits"]
    assert search["hits"][0]["chunk_id"]
    assert search["hits"][0]["trust_tier"] == "T3"
    assert "citation" in search["hits"][0]

    got = server.call_tool(
        TOOL_KB_GET_CHUNK, {"chunk_id": "docs-analise-espectral-001"}
    )
    assert got["ok"]
    assert "spectrum-report" in (got["chunk"]["body"] or "")

    sources = server.call_tool(TOOL_KB_LIST_SOURCES, {"trust_tier": "T3"})
    assert sources["ok"]
    assert any(s["source_id"] == "docs-analise-espectral" for s in sources["sources"])
    archive.close()


def test_mcp_rate_limit(tmp_path: Path) -> None:
    archive = SqliteArchive(tmp_path / "r.sqlite3")
    archive.migrate()
    _seed(archive)
    server = KbMcpServer(
        HybridRetriever(archive),
        rate_limiter=RateLimiter(max_calls=2, window_s=60.0),
    )
    assert server.call_tool(TOOL_KB_LIST_SOURCES, {})["ok"]
    assert server.call_tool(TOOL_KB_LIST_SOURCES, {})["ok"]
    blocked = server.call_tool(TOOL_KB_LIST_SOURCES, {})
    assert not blocked["ok"]
    assert blocked["error"] == "rate_limited"
    archive.close()


def test_mcp_jsonrpc_tools_call(tmp_path: Path) -> None:
    archive = SqliteArchive(tmp_path / "j.sqlite3")
    archive.migrate()
    _seed(archive)
    server = KbMcpServer(HybridRetriever(archive))
    init = handle_mcp_jsonrpc(
        server, {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}
    )
    assert init and init["result"]["serverInfo"]["name"] == "astrocitizen-kb"
    listed = handle_mcp_jsonrpc(
        server, {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
    )
    assert listed and len(listed["result"]["tools"]) == 4
    called = handle_mcp_jsonrpc(
        server,
        {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": TOOL_KB_SEARCH,
                "arguments": {"query": "AC-106", "limit": 2, "mode": "fts"},
            },
        },
    )
    assert called and called["result"]["content"][0]["type"] == "text"
    assert called["result"]["isError"] is False
    archive.close()

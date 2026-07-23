"""Adapter SQLite do ArchivePort + RetrieverPort FTS."""

from astrocitizen.adapters.sqlite.archive import SqliteArchive
from astrocitizen.adapters.sqlite.fts_retriever import SqliteFtsRetriever

__all__ = ["SqliteArchive", "SqliteFtsRetriever"]

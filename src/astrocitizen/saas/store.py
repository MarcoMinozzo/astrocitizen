"""Store mestre SaaS (scaffold AC-223) — SQLite por defeito; Postgres via DATABASE_URL depois."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any
from uuid import uuid4

from astrocitizen.shared.timeutil import utc_now_iso


class SaasMasterStore:
    """Persistência mínima: observations + network_submissions + idempotência."""

    def __init__(self, db_path: Path | str) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._migrate()

    def close(self) -> None:
        self._conn.close()

    def _migrate(self) -> None:
        self._conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS observations (
                id TEXT PRIMARY KEY,
                workspace_id TEXT NOT NULL,
                payload TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_saas_obs_ws
                ON observations(workspace_id, updated_at);

            CREATE TABLE IF NOT EXISTS network_submissions (
                id TEXT PRIMARY KEY,
                workspace_id TEXT NOT NULL,
                network TEXT NOT NULL,
                payload TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_saas_sub_ws
                ON network_submissions(workspace_id, network);

            CREATE TABLE IF NOT EXISTS sync_acks (
                client_op_id TEXT PRIMARY KEY,
                server_id TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS catalog_objects (
                id TEXT PRIMARY KEY,
                workspace_id TEXT NOT NULL,
                designation TEXT NOT NULL,
                payload TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_saas_cat_ws
                ON catalog_objects(workspace_id, updated_at);
            """
        )
        self._conn.commit()

    def apply_operation(self, op: dict[str, Any]) -> dict[str, Any]:
        client_op_id = str(op.get("client_op_id") or "")
        if not client_op_id:
            return {"client_op_id": "", "status": "failed", "reason": "missing client_op_id"}

        existing = self._conn.execute(
            "SELECT server_id, status FROM sync_acks WHERE client_op_id = ?",
            (client_op_id,),
        ).fetchone()
        if existing is not None:
            return {
                "client_op_id": client_op_id,
                "status": "accepted",
                "server_id": existing["server_id"],
                "idempotent": True,
            }

        entity = str(op.get("entity") or "")
        payload = op.get("payload") if isinstance(op.get("payload"), dict) else {}
        now = utc_now_iso()
        server_id = str(payload.get("id") or uuid4())

        if entity == "observation":
            ws = str(payload.get("workspace_id") or "")
            self._conn.execute(
                """
                INSERT INTO observations(id, workspace_id, payload, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    payload = excluded.payload,
                    updated_at = excluded.updated_at
                """,
                (server_id, ws, json.dumps(payload, ensure_ascii=False), now),
            )
        elif entity == "network_submission":
            ws = str(payload.get("workspace_id") or "")
            network = str(payload.get("network") or "")
            self._conn.execute(
                """
                INSERT INTO network_submissions(id, workspace_id, network, payload, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    payload = excluded.payload,
                    updated_at = excluded.updated_at
                """,
                (
                    server_id,
                    ws,
                    network,
                    json.dumps(payload, ensure_ascii=False),
                    now,
                ),
            )
        elif entity == "catalog_object":
            ws = str(payload.get("workspace_id") or "")
            desig = str(payload.get("designation") or payload.get("query_name") or "")
            self._conn.execute(
                """
                INSERT INTO catalog_objects(id, workspace_id, designation, payload, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    designation = excluded.designation,
                    payload = excluded.payload,
                    updated_at = excluded.updated_at
                """,
                (
                    server_id,
                    ws,
                    desig,
                    json.dumps(payload, ensure_ascii=False),
                    now,
                ),
            )
        else:
            return {
                "client_op_id": client_op_id,
                "status": "failed",
                "reason": f"entity desconhecida: {entity}",
            }

        self._conn.execute(
            """
            INSERT INTO sync_acks(client_op_id, server_id, status, created_at)
            VALUES (?, ?, 'accepted', ?)
            """,
            (client_op_id, server_id, now),
        )
        self._conn.commit()
        return {"client_op_id": client_op_id, "status": "accepted", "server_id": server_id}

    def list_observations(
        self, *, workspace_id: str | None = None, limit: int = 100
    ) -> list[dict[str, Any]]:
        lim = max(1, min(int(limit), 500))
        if workspace_id:
            rows = self._conn.execute(
                """
                SELECT payload FROM observations
                WHERE workspace_id = ?
                ORDER BY updated_at DESC
                LIMIT ?
                """,
                (workspace_id, lim),
            ).fetchall()
        else:
            rows = self._conn.execute(
                """
                SELECT payload FROM observations
                ORDER BY updated_at DESC
                LIMIT ?
                """,
                (lim,),
            ).fetchall()
        out: list[dict[str, Any]] = []
        for r in rows:
            try:
                out.append(json.loads(r["payload"]))
            except json.JSONDecodeError:
                continue
        return out
